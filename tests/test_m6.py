import json
import random
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from blackbox_twin.m6_run import attempt, load_protocol, run_campaign, source_hashes, summarize
from blackbox_twin.m6_targets import evaluation_inputs, render
from blackbox_twin.m6_train import IsolatedRandom, export_portable, typed_train, unsupported_train
from blackbox_twin.m51 import metrics

ROOT = Path(__file__).resolve().parents[1]


def test_concrete_twin_unknown_poisons_until_reset(tmp_path):
    known = {"operation": "stock", "arguments": {"quantity": 1}}
    inner = {
        "initial_state": "s",
        "actions": {"x": known},
        "transitions": {"s": {"x": {"next_state": "s", "output": {"payload": {"status": "ok"}}}}},
    }
    twin = tmp_path / "twin.py"
    export_portable({"schema_version": 4, "finite": inner, "reason": "concrete"}, twin)
    requests = [
        known,
        {"operation": "stock", "arguments": {"quantity": True}},
        known,
        {"control": "reset"},
        known,
    ]
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(twin)],
        input="".join(json.dumps(a) + "\n" for a in requests),
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    outputs = [json.loads(line) for line in result.stdout.splitlines()]
    assert outputs[0] == outputs[4] == {"status": "ok"}
    assert outputs[1]["bbt_unsupported"] and outputs[2]["bbt_unsupported"]
    assert outputs[3] == {"control": "reset", "ok": True}


def test_seed_stream_validation(tmp_path):
    p = tmp_path / "p.json"
    data = {
        "schema_version": 1,
        "learner_seeds": [11],
        "training_seeds": [21],
        "evaluation_seeds": [31],
        "budgets": {"A": [50]},
    }
    p.write_text(json.dumps(data))
    assert load_protocol(p) == data
    data["training_seeds"] = [11]
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="overlap"):
        load_protocol(p)


def test_native_rng_isolation():
    class Base:
        def find_cex(self, hypothesis):
            return random.random()

    class Oracle(IsolatedRandom, Base):
        training_state = random.Random(71).getstate()

    random.seed(17)
    previous = random.getstate()
    oracle, expected = Oracle(), random.Random(71)
    assert oracle.find_cex(None) == expected.random()
    assert oracle.find_cex(None) == expected.random()
    assert random.getstate() == previous


def test_attempt_reuse_and_corruption(tmp_path):
    calls = []

    def runner(folder):
        calls.append(1)
        folder.mkdir()
        (folder / "model.json").write_text("verified")
        (folder / "receipt.json").write_text(json.dumps({"complete": True}))
        return {"complete": True}

    folder, _ = attempt(tmp_path / "cell", runner)
    assert attempt(tmp_path / "cell", runner)[0] == folder and len(calls) == 1
    (folder / "model.json").write_text("corrupt")
    with pytest.raises(ValueError, match="integrity"):
        attempt(tmp_path / "cell", runner)


def test_interrupted_attempt_preserved(tmp_path):
    def interrupted(folder):
        folder.mkdir()
        (folder / "receipt.json").write_text(json.dumps({"complete": False}))
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        attempt(tmp_path / "cell", interrupted)

    def completed(folder):
        folder.mkdir()
        (folder / "receipt.json").write_text(json.dumps({"complete": True}))
        return {"complete": True}

    folder, _ = attempt(tmp_path / "cell", completed)
    assert folder.name == "attempt-001" and (folder.parent / "attempt-000/receipt.json").exists()


def test_false_supported_and_coverage_denominators():
    result = metrics(
        [{"category": "x"}],
        [[{"v": 1}, {"v": 2}, {"v": 3}]],
        [[{"v": 1}, {"v": 99}, {"bbt_unsupported": True}]],
        [[{"status": "LEGACY_CONCRETE"}, {"status": "LEGACY_CONCRETE"}, {"status": "UNSUPPORTED"}]],
    )
    values = result["groups"]["x"]
    assert values["conditional_accuracy"] == values["false_supported_rate"] == 0.5
    assert values["trace_fidelity"] == 0 and values["prediction_coverage"] == 2 / 3


def test_aggregation_is_target_weighted():
    rows = []
    for target, n, value in [("first", 5, 0.2), ("second", 1, 0.8)]:
        for _ in range(n):
            values = {
                name: value
                for name in (
                    "trace_fidelity",
                    "output_fidelity",
                    "prediction_coverage",
                    "conditional_accuracy",
                    "false_supported_rate",
                    "abstention_rate",
                )
            }
            rows.append(
                {
                    "target": target,
                    "track": "A",
                    "family": "test",
                    "method": "random",
                    "points": [{"ceiling": 10, "metrics": {"overall": values}}],
                    "training": {"costs": {"actions": 1, "resets": 1}, "status": "completed"},
                    "first_qualifying_ceiling": None,
                }
            )
    assert summarize(rows)["groups"][0]["metrics"]["trace_fidelity"]["median_target_mean"] == 0.5


def test_inventory_compatibility_no_fake_queries(tmp_path):
    result = unsupported_train(tmp_path / "unsupported", 500, "two_counter_model_class")
    assert result["costs"]["actions"] == result["costs"]["resets"] == 0
    with sqlite3.connect(tmp_path / "unsupported/observations.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_typed_budget_and_file_isolation(tmp_path, monkeypatch):
    contract = json.loads((ROOT / "examples/typed_wallet/contract.json").read_text())
    script = ROOT / "fixtures/targets/typed_wallet_process.py"
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.resolve() == script.resolve() or path.name in {
            "inputs.json",
            "evaluator-table.json",
        }:
            raise AssertionError("Training opened hidden source/evaluation")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    result = typed_train(contract, script, tmp_path / "run", 40, "hardened", 17, 71)
    assert result["status"] == "action_budget" and result["costs"]["actions"] == 40
    assert sum(v["actions"] for v in result["phase_costs"].values()) == 40


def test_historical_rare_and_generation_determinism():
    spec = {"track": "A", "family": "rare", "variant": 0, "target_seed": 71, "id": "rare"}
    a = render(ROOT, spec, {})
    assert a[0] == (ROOT / "evidence/m4-1/target-rare-access/oracle.py").read_text()
    assert evaluation_inputs(spec, a[1], None, 123) == evaluation_inputs(spec, a[1], None, 123)


def test_small_campaign_resume(tmp_path, monkeypatch):
    from blackbox_twin import m6_run

    manifest = tmp_path / "protocol.json"
    data = {
        "schema_version": 1,
        "source_sha256": source_hashes(),
        "learner_seeds": [17],
        "training_seeds": [71],
        "evaluation_seeds": [127],
        "finite_seed_count": 1,
        "typed_seed_count": 1,
        "reserved_values": [-7, -5, -3, 3, 6, 7],
        "budgets": {"A": [40]},
        "methods": {"A": ["aalpy-state-prefix"]},
        "targets": [
            {"id": "mini", "track": "A", "family": "easy", "variant": 0, "target_seed": 73}
        ],
    }
    manifest.write_text(json.dumps(data))
    summary = run_campaign(ROOT, manifest, tmp_path / "suite")
    monkeypatch.setattr(m6_run, "finite_train", lambda *a, **k: pytest.fail("Completed cell reran"))
    assert run_campaign(ROOT, manifest, tmp_path / "suite", resume=True) == summary
