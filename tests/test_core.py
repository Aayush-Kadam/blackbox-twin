import json
import sqlite3
import subprocess
import sys
from itertools import product
from pathlib import Path

import pytest
from pydantic import ValidationError

from blackbox_twin.contracts import Action, BehavioralModel, QueryBudget
from blackbox_twin.evaluation import sampled_evaluate
from blackbox_twin.learning import learn
from blackbox_twin.oracle import BudgetExhausted, OracleFailure, ProcessOracle
from blackbox_twin.storage import export_database


def test_reset_replay_and_observed_errors(session):
    word = ["create", "capture", "authorize", "capture", "refund", "cancel", "status"]
    observed = session.trace(word)
    assert observed == session.trace(word)
    assert observed[1].payload == {"error": "capture_not_allowed"}
    assert observed[-1].payload == {"status": "refunded"}
    assert session.costs.actions == 14
    assert session.costs.resets == 2


def test_physical_budget_no_overrun(session):
    session.budget = QueryBudget(max_actions=2)
    with pytest.raises(BudgetExhausted):
        session.trace(["create", "authorize", "capture"])
    assert session.costs.actions == 2
    assert session.costs.resets == 1
    assert session.exp is None


def test_reset_budget(session):
    session.budget = QueryBudget(max_resets=0)
    with pytest.raises(BudgetExhausted):
        session.trace(["status"])
    assert session.costs.resets == 0
    assert session.costs.actions == 0


def test_sequence_budget(session):
    session.budget = QueryBudget(max_sequence_length=1)
    with pytest.raises(BudgetExhausted):
        session.trace(["create", "status"])
    assert session.costs.actions == 1


def test_recording_matches_physical_counts(session, tmp_path):
    session.trace(["create", "status"])
    db = session.recorder.db
    assert db.execute("SELECT COUNT(*) FROM events WHERE kind='action'").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM events WHERE kind='reset'").fetchone()[0] == 1
    destination = tmp_path / "export.jsonl"
    db_path = Path(db.execute("PRAGMA database_list").fetchone()[2])
    export_database(db_path, destination)
    rows = [json.loads(line) for line in destination.read_text().splitlines()]
    assert any(row["table"] == "events" for row in rows)


def test_strict_contracts():
    with pytest.raises(ValidationError):
        QueryBudget(max_actions=-1)
    with pytest.raises(ValidationError):
        Action(operation="create", surprise="not allowed")
    with pytest.raises(ValidationError):
        BehavioralModel(initial_state="missing", actions={}, transitions={})


@pytest.mark.parametrize(
    "body, expected",
    [
        ("import time; time.sleep(10)", "timeout"),
        ("print('not-json', flush=True)", "transport_failure"),
        ("raise SystemExit(0)", "process_eof"),
        ("print('x'*1000, flush=True)", "response_too_large"),
        ("print('{}', flush=True)", "reset_not_acknowledged"),
    ],
)
def test_transport_failures(tmp_path, body, expected):
    script = tmp_path / "bad.py"
    script.write_text(body)
    # Non-timeout cases must allow normal Windows interpreter startup under load.
    timeout = 0.15 if expected == "timeout" else 2.0
    oracle = ProcessOracle(script, timeout=timeout, max_response_bytes=100)
    try:
        with pytest.raises(OracleFailure, match=expected):
            oracle.reset()
        assert oracle.process.poll() is not None
    finally:
        oracle.close()


def test_learning_and_unseen_long_sequences(session, tmp_path):
    session.verify_reset()
    model, stats = learn(session, tmp_path / "model.json", seed=7, walks=20)
    assert len(model.transitions) == 6
    restored = BehavioralModel.model_validate_json((tmp_path / "model.json").read_text())
    assert restored == model
    for word in product(["create", "authorize", "capture"], repeat=4):
        assert model.predict(word) == session.trace(word)
    result = sampled_evaluate(
        session, model, count=25, seed=998, minimum_length=15, maximum_length=25
    )
    assert result["trace_matches"] == 25
    assert stats["learning_rounds"] >= 1
    # AALpy cache counters are logical; the authoritative costs are the persisted events.
    assert stats["cache_saved"] > 0
    count = session.recorder.db.execute(
        "SELECT COUNT(*) FROM events WHERE kind='action'"
    ).fetchone()[0]
    assert count == session.costs.actions


def test_standalone_twin(session, tmp_path):
    from blackbox_twin.synthesis import generate_twin

    model, _ = learn(session, tmp_path / "model.json", walks=10)
    clean = tmp_path / "clean"
    clean.mkdir()
    twin = clean / "twin.py"
    generate_twin(model, twin)
    word = ["create", "authorize", "capture", "refund", "status"]
    input_text = "\n".join(json.dumps(session.target.actions[a].model_dump()) for a in word)
    result = subprocess.run(
        [sys.executable, "-I", str(twin)],
        cwd=clean,
        input=input_text + '\n{"operation":"unseen"}\n',
        capture_output=True,
        text=True,
        timeout=3,
        check=True,
    )
    outputs = [json.loads(line) for line in result.stdout.splitlines()]
    assert outputs[:-1] == [o.payload for o in model.predict(word)]
    assert outputs[-1]["bbt_unsupported"] is True
    assert list(clean.iterdir()) == [twin]


def test_no_target_imports():
    import ast

    source_root = Path(__file__).resolve().parents[1] / "src/blackbox_twin"
    for file in source_root.glob("*.py"):
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("fixtures")
            elif isinstance(node, ast.Import):
                assert all(not alias.name.startswith("fixtures") for alias in node.names)


def test_heldout_excludes_training(session, tmp_path):
    model, _ = learn(session, tmp_path / "model.json", walks=5)
    session.phase = "held-out"
    excluded = [("create", "create")]
    sampled_evaluate(
        session, model, count=20, minimum_length=2, maximum_length=2, excluded=excluded
    )
    words = [
        tuple(json.loads(row[0]))
        for row in session.recorder.db.execute(
            "SELECT actions FROM experiments WHERE phase='held-out'"
        )
    ]
    assert len(set(words)) == 20
    assert not set(words).intersection(excluded)


def test_unknown_database_version(tmp_path):
    from blackbox_twin.storage import Recorder

    path = tmp_path / "future.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="version"):
        Recorder(path, {})
