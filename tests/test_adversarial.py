import json
from itertools import product
from pathlib import Path

import pytest

from blackbox_twin.contracts import Action, QueryBudget, Target
from blackbox_twin.learning import learn
from blackbox_twin.oracle import BudgetExhausted, OracleFailure, ProcessOracle, Session
from blackbox_twin.storage import Recorder


def test_tiny_two_state_recovery(tmp_path):
    target = Target(
        target_id="toggle",
        version="1",
        executable="unused",
        authorization="owned-local-fixture",
        actions={s: Action(operation=s) for s in ("flip", "read")},
    )
    script = Path(__file__).resolve().parents[1] / "fixtures/targets/toggle_process.py"
    recorder = Recorder(tmp_path / "tiny.sqlite", {})
    oracle = ProcessOracle(script)
    session = Session(oracle, target, QueryBudget(), recorder)
    try:
        model, _ = learn(session, tmp_path / "tiny.json", walks=20)
        assert len(model.transitions) == 2
        # Ground truth remains in the evaluator, not the learner.
        for length in range(1, 6):
            for word in product(("flip", "read"), repeat=length):
                state, expected = False, []
                for symbol in word:
                    if symbol == "flip":
                        state = not state
                    expected.append({"lit": state})
                assert [o.payload for o in model.predict(word)] == expected
    finally:
        session.post()
        oracle.close()
        recorder.close("test_completed")


def test_reset_ack_is_insufficient(session):
    original = session.oracle.reset
    calls = 0

    def faulty_reset():
        nonlocal calls
        calls += 1
        if calls == 1:
            return original()
        return {"control": "reset", "ok": True}

    session.oracle.reset = faulty_reset
    with pytest.raises(OracleFailure, match="mismatch"):
        session.verify_reset()


def test_zero_budget_cli_preserves_failure(tmp_path):
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "budget-run"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "blackbox_twin.cli",
            "learn",
            "--target",
            str(root / "examples/order_processing/target.json"),
            "--out",
            str(out),
            "--budget",
            "0",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode == 2, process.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert summary["physical_costs"]["actions"] == 0
    assert summary["status"].startswith("budget_exhausted")
    assert not summary["checkpoint_exists"]


@pytest.mark.parametrize("limit, checkpoint_expected", [(800, False), (1000, True)])
def test_budget_exhaustion_preserves_hypothesis(session, tmp_path, limit, checkpoint_expected):
    session.budget = QueryBudget(max_actions=limit)
    path = tmp_path / "checkpoint.json"
    with pytest.raises(BudgetExhausted):
        learn(session, path, walks=100)
    assert path.exists() == checkpoint_expected
    assert session.costs.actions == limit


def test_oversize_request(session):
    with pytest.raises(OracleFailure, match="request_too_large"):
        session.oracle.step(Action(operation="x", arguments={"text": "x" * 2000}))


def test_cleanup_failure_still_writes_summary(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from blackbox_twin.cli import run_learning

    original = ProcessOracle.close

    def failing_cleanup(self):
        original(self)
        raise OSError("injected cleanup failure")

    monkeypatch.setattr(ProcessOracle, "close", failing_cleanup)
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "cleanup-run"
    args = SimpleNamespace(
        target=root / "examples/order_processing/target.json",
        out=out,
        budget=0,
        reset_budget=10,
        seed=7,
        walks=1,
        walk_length=1,
    )
    assert run_learning(args) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "cleanup_failed"
    assert "injected cleanup failure" in summary["cleanup_error"]


def test_launch_failure_marks_run_failed(tmp_path, monkeypatch):
    import sqlite3

    from blackbox_twin import cli

    database = tmp_path / "launch.sqlite"
    recorder = Recorder(database, {})

    def failed_launch(script):
        raise OSError("injected startup failure")

    monkeypatch.setattr(cli, "ProcessOracle", failed_launch)
    with pytest.raises(OSError, match="startup failure"):
        cli.open_session(None, None, None, recorder, "test")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT status FROM runs").fetchone()[0] == "initialization_failed"
