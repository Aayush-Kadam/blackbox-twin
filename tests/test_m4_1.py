import json

import pytest
from aalpy.oracles import StatePrefixEqOracle

from blackbox_twin.contracts import Action, BehavioralModel, Observation, Transition
from blackbox_twin.defaults import DEFAULT_STRATEGY, STRATEGIES, learning_options
from blackbox_twin.planner_diagnostics import DiagnosticPlanner
from blackbox_twin.planning import ExperimentPlanner, PlanningContext


def one_state():
    return BehavioralModel(
        initial_state="s",
        actions={a: Action(operation=a) for a in "ab"},
        transitions={
            "s": {
                a: Transition(next_state="s", output=Observation(payload={"ok": True}))
                for a in "ab"
            }
        },
    )


def fixed(monkeypatch, planner, words):
    monkeypatch.setattr(planner, "candidates", lambda context: words)
    return planner


def test_coverage_toggle_changes_order(monkeypatch):
    context = PlanningContext(one_state(), {("b",): True}, remaining_actions=10)
    full = fixed(monkeypatch, ExperimentPlanner(), [("a", "a"), ("b", "b")]).propose(context)
    off = fixed(monkeypatch, ExperimentPlanner("no-coverage"), [("a", "a"), ("b", "b")]).propose(
        context
    )
    assert full.actions == ("a", "a")
    assert off.actions == ("b", "b")  # Equal scores: descending lexical tie-break.
    assert full.score == pytest.approx(2.5 / 3)
    assert off.score == pytest.approx(1 / 3)


def test_separator_toggle_changes_score_and_order(monkeypatch):
    model = one_state()
    model.transitions["s"]["a"].next_state = "t"
    model.transitions["t"] = {
        a: Transition(next_state="s", output=Observation(payload={"ok": False})) for a in "ab"
    }
    model = BehavioralModel.model_validate(model.model_dump())
    context = PlanningContext(model, remaining_actions=10)
    full = fixed(monkeypatch, ExperimentPlanner(), [("a",), ("b",)]).propose(context)
    off = fixed(monkeypatch, ExperimentPlanner("no-suffix"), [("a",), ("b",)]).propose(context)
    assert full.actions == ("a",) and off.actions == ("b",)
    assert full.score - off.score == pytest.approx(0.25)


def test_cost_toggle_and_atomic_budget(monkeypatch):
    context = PlanningContext(one_state(), remaining_actions=3)
    words = [("a",), ("b", "b", "b")]
    full = fixed(monkeypatch, ExperimentPlanner(), words).propose(context)
    off = fixed(monkeypatch, ExperimentPlanner("no-cost"), words).propose(context)
    assert full.actions == ("a",) and off.actions == ("b", "b", "b")
    context.remaining_actions = 2
    assert fixed(monkeypatch, ExperimentPlanner("no-cost"), words).propose(context).actions == (
        "a",
    )
    context.history[("a",)] = True
    assert fixed(monkeypatch, ExperimentPlanner(), words).propose(context) is None


def test_diagnostics_do_not_change_choices_and_are_bounded():
    context = PlanningContext(one_state(), remaining_actions=40)
    plain = ExperimentPlanner(seed=19, pool_size=8)
    logged = DiagnosticPlanner(seed=19, pool_size=8, limit=2)
    for _ in range(4):
        a, b = plain.propose(context), logged.propose(context)
        assert a == b
        context.history[a.actions] = True
    assert len(logged.records) == 2 and logged.dropped == 2
    record = json.loads(json.dumps(logged.records[0]))
    assert record["eligible"] <= record["unique_length_filtered"]
    assert record["score"] == record["top_candidates"][0]["score"]
    assert all(r["cost"] == len(r["actions"]) for r in record["top_candidates"])
    assert "hidden_state" not in record


def test_default_native_and_other_strategies_preserved():
    from types import SimpleNamespace

    options = learning_options()
    sul = SimpleNamespace(session=SimpleNamespace())
    native = options["equivalence_factory"](["a"], sul)
    assert DEFAULT_STRATEGY == "aalpy-state-prefix"
    assert isinstance(native, StatePrefixEqOracle)
    assert native.steps_per_walk == 12
    for strategy in STRATEGIES:
        assert learning_options(strategy)["equivalence_factory"](["a"], sul)
    with pytest.raises(ValueError):
        learning_options("invented")


def test_cli_default_is_visible(capsys, monkeypatch):
    from blackbox_twin import cli

    monkeypatch.setattr("sys.argv", ["bbt", "learn", "--help"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "aalpy-state-prefix" in help_text and "cost-aware" in help_text
    captured = []
    monkeypatch.setattr(cli, "run_learning", lambda args: captured.append(args) or 0)
    monkeypatch.setattr("sys.argv", ["bbt", "learn", "--target", "unused", "--out", "unused"])
    assert cli.main() == 0
    assert captured[0].strategy == DEFAULT_STRATEGY
    assert captured[0].walk_length == 12 and captured[0].walks == 25
