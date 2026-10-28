import json
from pathlib import Path

import pytest

from blackbox_twin.benchmark import Checkpoints, CheckpointSession, run_suite, train_cell
from blackbox_twin.benchmark_targets import generate_target
from blackbox_twin.contracts import Action, BehavioralModel, Observation, QueryBudget, Transition
from blackbox_twin.oracle import BudgetExhausted, OracleFailure, ProcessOracle, Session
from blackbox_twin.planner_oracles import ReplayCacheSUL
from blackbox_twin.planning import (
    ExperimentPlanner,
    PlanningContext,
    access_paths,
    distinguishing_suffixes,
)
from blackbox_twin.storage import Recorder

ROOT = Path(__file__).resolve().parents[1]


def machine(unreachable=False):
    actions = {s: Action(operation=s) for s in ("a", "b")}
    rows = {
        s: {
            a: Transition(
                next_state="S1" if a == "a" else "S0",
                output=Observation(payload={"lit": s == "S1"}),
            )
            for a in actions
        }
        for s in ("S0", "S1")
    }
    if unreachable:
        rows["hidden"] = {
            a: Transition(next_state="hidden", output=Observation(payload={})) for a in actions
        }
    return BehavioralModel(initial_state="S0", actions=actions, transitions=rows)


def test_access_and_separators():
    model = machine(unreachable=True)
    assert access_paths(model) == {"S0": (), "S1": ("a",)}
    assert distinguishing_suffixes(model) == [("a",)]


@pytest.mark.parametrize(
    "method", ["random", "bfs", "cost-aware", "no-cost", "no-coverage", "no-suffix"]
)
def test_planner_seed_deduplication_and_cost(method):
    context = PlanningContext(machine(), {}, remaining_actions=4)
    left, right = ExperimentPlanner(method, 9), ExperimentPlanner(method, 9)
    assert left.propose(context) == right.propose(context)
    candidates = left.candidates(context)
    assert len(candidates) == len(set(candidates))
    proposal = ExperimentPlanner(method, 9).propose(context)
    if proposal:
        assert proposal.estimated_actions == len(proposal.actions) <= 4
        assert proposal.estimated_resets == 1
        assert proposal.reasons


def test_empty_candidates_and_budget():
    model = BehavioralModel(initial_state="S0", actions={}, transitions={"S0": {}})
    assert ExperimentPlanner().propose(PlanningContext(model, remaining_actions=10)) is None
    assert ExperimentPlanner().propose(PlanningContext(machine(), remaining_actions=0)) is None


def test_no_known_word_is_charged_as_new():
    context = PlanningContext(machine(), {("a",): True}, remaining_actions=1)
    proposal = ExperimentPlanner().propose(context)
    assert proposal.actions == ("b",)


def test_cache_replays_whole_prefix_cost(tmp_path):
    target, script = generate_target(tmp_path / "target", "random", 11)
    recorder = Recorder(tmp_path / "cache.sqlite", {})
    session = Session(ProcessOracle(script), target, QueryBudget(max_actions=3), recorder)
    sul = ReplayCacheSUL(session)
    try:
        first = sul.query(("a",))
        assert sul.query(("a",)) == first
        assert session.costs.actions == 1 and session.costs.resets == 1
        sul.query(("a", "b"))
        assert session.costs.actions == 3 and session.costs.resets == 2
        with pytest.raises(BudgetExhausted):
            sul.query(("a", "a"))
        assert session.costs.actions == 3
    finally:
        session.post("test_completed")
        session.oracle.close()
        recorder.close("test_completed")


def test_nondeterminism_on_prefix_replay(tmp_path):
    from blackbox_twin.contracts import Target

    class Flaky:
        flips = -1

        def reset(self):
            self.flips += 1

        def step(self, action):
            return Observation(payload={"flip": self.flips})

    target = Target(
        target_id="flaky",
        version="1",
        executable="unused",
        authorization="owned-local-fixture",
        actions=machine().actions,
    )
    recorder = Recorder(tmp_path / "flaky.sqlite", {})
    session = Session(Flaky(), target, QueryBudget(), recorder)
    sul = ReplayCacheSUL(session)
    try:
        sul.query(("a",))
        with pytest.raises(OracleFailure, match="nondeterminism"):
            sul.query(("a", "b"))
    finally:
        session.post()
        recorder.close("test_completed")


def test_checkpoints_do_not_receive_future_models(tmp_path):
    target, script = generate_target(tmp_path / "target", "random", 11)
    recorder = Recorder(tmp_path / "points.sqlite", {})
    session = CheckpointSession(ProcessOracle(script), target, QueryBudget(), recorder)
    tracker = Checkpoints(session, tmp_path, [2, 4])
    session.tracker = tracker
    try:
        session.trace(["a", "a", "a"])
        assert tracker.points[2]["model"] is None
        tracker.on_model(machine())
        assert tracker.points[2]["model"] is None
        assert tracker.model_cost == 3
    finally:
        session.oracle.close()
        recorder.close("test_completed")


def pilot_config():
    config = json.loads((ROOT / "benchmarks/manifests/m4-development.json").read_text())
    config.update(
        families=["delayed"],
        seeds=[11, 12],
        budgets=[30, 100],
        evaluation_count=4,
        methods=["random", "bfs", "aalpy-random-w", "aalpy-state-prefix", "cost-aware"],
    )
    config["workflow_source"] = str(ROOT / "fixtures/targets/order_process.py")
    return config


def test_paired_benchmark_fairness_resume_and_separation(tmp_path, monkeypatch):
    config = pilot_config()
    manifest = tmp_path / "protocol.json"
    manifest.write_text(json.dumps(config))
    out = tmp_path / "suite"
    summary = run_suite(manifest, out)
    assert summary["completed_cells"] == summary["expected_cells"] == 10
    for seed in config["seeds"]:
        cells = [
            json.loads(p.read_text()) for p in (out / "delayed" / str(seed)).glob("*/result.json")
        ]
        assert len({c["evaluation_sha256"] for c in cells}) == 1
        assert len({c["target_contract_sha256"] for c in cells}) == 1
        assert all(c["training"]["costs"]["actions"] <= 100 for c in cells)
        assert all(p["actual_actions"] <= p["ceiling"] for c in cells for p in c["points"])
        assert (
            len(list((out / "delayed" / str(seed)).glob("*/attempt-000/observations.sqlite"))) == 5
        )
    from blackbox_twin import benchmark

    monkeypatch.setattr(benchmark, "train_cell", lambda *args: pytest.fail("Completed cell reran"))
    assert run_suite(manifest, out, resume=True) == summary


def test_learner_cannot_open_target_source_or_evaluation(tmp_path, monkeypatch):
    target, script = generate_target(tmp_path / "target", "delayed", 11)
    config = pilot_config()
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.resolve() == script.resolve() or "evaluation" in path.parts:
            raise AssertionError("Disallowed learner file read")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    result = train_cell(target, script, tmp_path / "training", config, "cost-aware", 11)
    assert result["costs"]["actions"] <= 100


def test_interrupted_cell_keeps_evidence(tmp_path, monkeypatch):
    from blackbox_twin import benchmark

    target, script = generate_target(tmp_path / "target", "delayed", 11)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(benchmark, "learn", interrupted)
    with pytest.raises(KeyboardInterrupt):
        train_cell(target, script, tmp_path / "interrupted", pilot_config(), "random", 11)
    saved = json.loads((tmp_path / "interrupted/training.json").read_text())
    assert saved["status"] == "interrupted"
    assert saved["costs"]["actions"] > 0


def test_planner_integrates_with_real_m3_refinement(tmp_path):
    from blackbox_twin.refinement import run_loop

    target, script = generate_target(tmp_path / "target", "delayed", 12)
    result = run_loop(
        target,
        script,
        tmp_path / "loop",
        QueryBudget(max_actions=3000),
        strategy="cost-aware",
        candidates=220,
        max_iterations=1,
        refinement_walks=2,
    )
    assert result["resolved_counterexamples"] == 1, result
    assert result["revisions"][1]["states"] > result["revisions"][0]["states"]
    assert result["iterations"][0]["regressions"]["new_regressions"] == 0
    assert (tmp_path / "loop/revisions/001/twin.py").exists()


def test_learning_curve_and_censored_threshold():
    from blackbox_twin.benchmark_summary import aulc

    points = [{"ceiling": 100, "trace_fidelity": 0.5}, {"ceiling": 200, "trace_fidelity": 1.0}]
    assert aulc(points) == 0.25  # f(0)=0, then left-constant 0.5 over [100,200).


def test_confirmatory_random_streams_are_separate():
    config = json.loads((ROOT / "benchmarks/manifests/m4-confirmatory.json").read_text())
    generated = set(config["seeds"])
    selected = {s + config["selection_seed_offset"] for s in generated}
    evaluated = {s + config["evaluation_seed_offset"] for s in generated}
    assert not generated & selected and not generated & evaluated and not selected & evaluated


def test_candidate_component_ablations_are_real():
    context = PlanningContext(machine(), remaining_actions=10)
    full = ExperimentPlanner("cost-aware", seed=3).propose(context)
    no_cost = ExperimentPlanner("no-cost", seed=3).propose(context)
    no_suffix = ExperimentPlanner("no-suffix", seed=3).propose(context)
    assert full.score != no_cost.score
    assert all(
        reason == "hypothesis-separator=0.0"
        for reason in no_suffix.reasons
        if reason.startswith("hypothesis-separator=")
    )


def test_failed_or_unreached_cells_are_not_successes(tmp_path):
    from blackbox_twin.benchmark_summary import summarize

    config = {"families": ["delayed"], "seeds": [1], "methods": ["random"], "budgets": [100]}
    (tmp_path / "config.json").write_text(json.dumps({"protocol": config}))
    folder = tmp_path / "delayed/1/random"
    folder.mkdir(parents=True)
    result = {
        "family": "delayed",
        "seed": 1,
        "method": "random",
        "points": [{"ceiling": 100, "trace_fidelity": 0.5}],
        "training": {
            "status": "failed:timeout",
            "costs": {"actions": 50, "resets": 10},
            "planner_seconds": 0.0,
            "wall_seconds": 1.0,
            "counterexamples": [],
        },
    }
    (folder / "result.json").write_text(json.dumps(result))
    summary = summarize(tmp_path)
    assert summary["methods"]["random"]["threshold_reached"] == 0
    assert summary["methods"]["random"]["threshold_median_among_reached"] is None
    assert summary["methods"]["random"]["failures"]
    assert summary["performance_hypothesis"] == "INCONCLUSIVE"
