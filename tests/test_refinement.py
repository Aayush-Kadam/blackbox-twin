import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from blackbox_twin.cli import load_target
from blackbox_twin.contracts import BehavioralModel, Costs, QueryBudget
from blackbox_twin.counterexamples import Corpus, model_id
from blackbox_twin.experiments import discover, guided_sequences
from blackbox_twin.m3_evaluation import evaluate_pair, freeze_sequences, read_prior_traces
from blackbox_twin.oracle import ProcessOracle, Session
from blackbox_twin.refinement import executable_runner, run_loop
from blackbox_twin.storage import Recorder

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def authentic_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("authentic-m3")
    target, script = load_target(ROOT / "examples/delayed/target.json")
    frozen = out / "sequences.json"
    freeze_sequences(target, frozen, seed=12499, count=20)
    before = frozen.read_bytes()
    summary = run_loop(
        target,
        script,
        out / "loop",
        QueryBudget(max_actions=6000, total_seconds=180.0),
        max_iterations=2,
    )
    initial = BehavioralModel.model_validate_json(
        (out / "loop/revisions/000/model.json").read_text()
    )
    final = BehavioralModel.model_validate_json((out / "loop/revisions/001/model.json").read_text())
    evaluation = evaluate_pair(
        target,
        script,
        initial,
        final,
        frozen,
        out / "loop/observations.sqlite",
        out / "evaluation",
        QueryBudget(total_seconds=180.0),
    )
    assert frozen.read_bytes() == before
    return out, target, script, summary, initial, final, evaluation


def test_authentic_end_to_end_refinement(authentic_run):
    out, _, _, summary, initial, final, _ = authentic_run
    assert summary["resolved_counterexamples"] == 1
    assert summary["status"] == "no_counterexample_under_search_policy"
    assert [r["states"] for r in summary["revisions"]] == [1, 5]
    assert model_id(initial) != model_id(final)
    iteration = summary["iterations"][0]
    assert len(iteration["minimized_actions"]) < len(iteration["original_actions"])
    regressions = iteration["regressions"]
    assert regressions["checked"] == regressions["passed"]
    assert regressions["previously_passing"] == regressions["previously_passing_preserved"]
    assert regressions["new_regressions"] == 0
    stats = summary["revisions"][1]["learning_statistics"]
    assert stats["learning_rounds"] >= 2
    assert stats["confirmed_counterexamples_returned"]
    record = Corpus.read(next((out / "loop/counterexamples").glob("*/discovery.json")))
    case = record.minimization.minimized
    assert case.is_mismatch and record.minimization.locally_minimal
    assert final.predict(case.actions) == case.original
    # Tail outputs happen to match; RS must receive the FIRST-divergence prefix instead.
    discovery = record.minimization.original
    assert initial.predict(discovery.actions)[-1] == discovery.original[-1]
    returned = stats["confirmed_counterexamples_returned"][0]
    assert returned == discovery.actions[: discovery.first_divergence + 1]
    assert (out / "loop/revisions/000/twin.py").exists()
    assert (out / "loop/revisions/001/twin.py").exists()
    assert (out / "loop/revisions/001/hypothesis-002.json").exists()


def test_phase_accounting_and_heldout_integrity(authentic_run):
    out, target, _, summary, _, _, evaluation = authentic_run
    for side in ("original", "twin"):
        prefix = "twin:" if side == "twin" else ""
        phases = [
            cost
            for phase, cost in summary["phase_costs"].items()
            if phase.startswith("twin:") == bool(prefix)
        ]
        assert sum(c["actions"] for c in phases) == summary[f"{side}_costs"]["actions"]
        assert sum(c["resets"] for c in phases) == summary[f"{side}_costs"]["resets"]
    assert summary["original_costs"]["actions"] <= 6000
    assert evaluation["status"] == "completed"
    assert evaluation["full_sequence_training_overlap"] == 0
    assert evaluation["scores"]["refined"]["trace_matches"] == 20
    assert evaluation["scores"]["initial"]["trace_matches"] < 20
    with pytest.raises(ValueError, match="Held-out observations"):
        read_prior_traces(out / "evaluation/observations.sqlite", target)


def test_model_guided_discovery_and_replay(authentic_run, tmp_path):
    out, target, script, _, initial, _, _ = authentic_run
    recorder = Recorder(tmp_path / "guided.sqlite", {"target": target.model_dump()})
    original = Session(ProcessOracle(script), target, QueryBudget(), recorder, "guided-search")
    try:
        with executable_runner(original, out / "loop/revisions/000/twin.py", Costs()) as runner:
            found = discover(runner, guided_sequences(initial, depth=5, count=200))
            assert found.is_mismatch
            assert runner.run(found.actions) == found
    finally:
        original.oracle.close()
        recorder.close("test_completed")


def test_counterexample_cli_replay(authentic_run, tmp_path):
    out, _, _, _, _, _, _ = authentic_run
    case = next((out / "loop/counterexamples").glob("*/discovery.json"))
    for revision, code in (("000", 3), ("001", 0)):
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "blackbox_twin.cli",
                "counterexample",
                "replay",
                "--target",
                str(ROOT / "examples/delayed/target.json"),
                "--model",
                str(out / f"loop/revisions/{revision}/model.json"),
                "--case",
                str(case),
                "--out",
                str(tmp_path / revision),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert process.returncode == code, process.stderr
        assert (tmp_path / revision / "comparison.json").exists()


@pytest.mark.parametrize(
    "budget,iterations,expected",
    [
        (0, 2, "BudgetExhausted:physical_action_budget"),
        (6000, 0, "max_iterations_reached"),
    ],
)
def test_loop_stopping_limits(tmp_path, budget, iterations, expected):
    target, script = load_target(ROOT / "examples/delayed/target.json")
    summary = run_loop(
        target,
        script,
        tmp_path / "stop",
        QueryBudget(max_actions=budget),
        max_iterations=iterations,
    )
    assert summary["status"] == expected
    assert len(summary["iterations"]) <= iterations
    assert summary["original_costs"]["actions"] <= budget


def test_budget_stop_records_pending_refinement_outcome(tmp_path):
    target, script = load_target(ROOT / "examples/delayed/target.json")
    root = tmp_path / "partial-refinement"
    summary = run_loop(target, script, root, QueryBudget(max_actions=300), max_iterations=2)
    assert summary["status"] == "BudgetExhausted:physical_action_budget"
    assert summary["original_costs"]["actions"] == 300
    assert summary["resolved_counterexamples"] == 0
    outcome = json.loads(next((root / "counterexamples").glob("*/outcome-*.json")).read_text())
    assert outcome["status"] == "refinement_not_completed"


def test_failed_refinement_is_reported(tmp_path, monkeypatch):
    from blackbox_twin import refinement

    real_learn, previous = refinement.learn, []

    def injected_no_progress(session, model_path, **options):
        if not previous:
            result = real_learn(session, model_path, **options)
            previous.append(result[0])
            return result
        # Explicit failure injection, never counted as authentic learning evidence.
        model_path.write_text(previous[0].model_dump_json(indent=2))
        return previous[0], {"fault_injection": "learner made no progress"}

    monkeypatch.setattr(refinement, "learn", injected_no_progress)
    target, script = load_target(ROOT / "examples/delayed/target.json")
    result = run_loop(target, script, tmp_path / "no-progress", QueryBudget(), max_iterations=3)
    assert result["status"] == "refinement_failed_no_progress"
    assert result["resolved_counterexamples"] == 0
    assert len(result["iterations"]) == 1
    assert result["iterations"][0]["regressions"]["failures"]


def test_blackbox_loop_does_not_open_target_source(tmp_path, monkeypatch):
    target, script = load_target(ROOT / "examples/delayed/target.json")
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.resolve() == script:
            raise AssertionError("Learner attempted to inspect hidden target source")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    result = run_loop(target, script, tmp_path / "blackbox", QueryBudget(), max_iterations=1)
    assert result["resolved_counterexamples"] == 1


def test_existing_model_requires_evidence(authentic_run, tmp_path):
    _, target, script, _, initial, _, _ = authentic_run
    with pytest.raises(ValueError, match="prior observation corpus"):
        run_loop(target, script, tmp_path / "missing", QueryBudget(), initial_model=initial)


def test_repeated_hypothesis_guard(authentic_run, tmp_path, monkeypatch):
    from aalpy.automata import MealyMachine, MealyState

    from blackbox_twin import learning
    from blackbox_twin.refinement import encode_samples

    out, target, script, _, initial, _, _ = authentic_run
    recorder = Recorder(tmp_path / "stalled.sqlite", {})
    session = Session(ProcessOracle(script), target, QueryBudget(), recorder)
    record = Corpus.read(next((out / "loop/counterexamples").glob("*/discovery.json")))
    case = record.minimization.minimized
    confirmed = encode_samples([(case.actions, [o.payload for o in case.original])])

    def injected_stall(alphabet, sul, eq, *args, **kwargs):
        state = MealyState("S0")
        for action in alphabet:
            state.transitions[action] = state
            state.output_fun[action] = json.dumps(
                initial.transitions[initial.initial_state][action].output.payload,
                sort_keys=True,
                separators=(",", ":"),
            )
        hypothesis = MealyMachine(state, [state])
        eq.find_cex(hypothesis)
        eq.find_cex(hypothesis)

    monkeypatch.setattr(learning, "run_Lstar", injected_stall)
    try:
        with pytest.raises(learning.LearningStalled, match="repeated_hypothesis"):
            learning.learn(session, tmp_path / "stalled.json", confirmed=confirmed)
        assert session.costs.actions == 0
    finally:
        session.oracle.close()
        recorder.close("test_completed")


def test_paired_evaluation_rejects_training_overlap(authentic_run, tmp_path):
    out, target, script, _, initial, final, _ = authentic_run
    dataset = json.loads((out / "sequences.json").read_text())
    with sqlite3.connect(out / "loop/observations.sqlite") as db:
        word = json.loads(
            db.execute(
                "SELECT actions FROM experiments WHERE phase='initial-learning' AND actions!='[]'"
            ).fetchone()[0]
        )
    dataset["sequences"] = [word]
    file = tmp_path / "leaked.json"
    file.write_text(json.dumps(dataset))
    with pytest.raises(ValueError, match="overlap"):
        evaluate_pair(
            target,
            script,
            initial,
            final,
            file,
            out / "loop/observations.sqlite",
            tmp_path / "invalid",
            QueryBudget(),
        )
