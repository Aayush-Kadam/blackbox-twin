"""Optional M7 transport tests; run with [workbench,workbench-test] installed."""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from blackbox_twin.contracts import BehavioralModel, Observation  # noqa: E402
from blackbox_twin.differential import compare_traces  # noqa: E402
from blackbox_twin.m7_data import Evidence, contained, db_counts  # noqa: E402
from blackbox_twin.synthesis import generate_twin  # noqa: E402
from blackbox_twin.workbench import create_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"X-BBT-Local": "1"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(ROOT, tmp_path / "runs")) as value:
        yield value


def test_persisted_model_serialization_export_and_costs(client):
    result = client.get("/api/experiments/m3-replay")
    assert result.status_code == 200
    data = result.json()
    assert data["mode"] == "persisted replay" and not data["equivalence_proven"]
    assert [
        len(BehavioralModel.model_validate(r["model"]).transitions) for r in data["models"]
    ] == [1, 5]
    assert data["physical_training"] == {"actions": 1855, "resets": 288}
    db = ROOT / "evidence/m3-demo/loop/observations.sqlite"
    assert db_counts(db, twin=True) == {
        k: data["summary"]["twin_costs"][k] for k in ("actions", "resets")
    }
    exported = client.get("/api/experiments/m3-replay/export/1/model")
    assert exported.json() == data["models"][1]["model"]
    assert "attachment" in exported.headers["content-disposition"]
    assert client.get("/api/experiments/m3-replay/export/1/twin").status_code == 200


def test_trace_comparison_and_counterexample_presentation(client):
    data = client.get("/api/experiments/m3-replay").json()
    shrink = data["counterexamples"][0]["minimization"]
    assert len(shrink["original"]["actions"]) == 10
    assert shrink["minimized"]["actions"] == ["advance"] * 4 + ["commit"]
    for key in ("original", "minimized"):
        value = shrink[key]
        comparison = compare_traces(
            value["actions"],
            [Observation.model_validate(v) for v in value["original"]],
            [Observation.model_validate(v) for v in value["twin"]],
        )
        assert comparison.first_divergence == value["first_divergence"]
        assert comparison.raw_original == value["raw_original"]
        assert comparison.raw_twin == value["raw_twin"]
        assert comparison.is_mismatch
    assert shrink["minimized"]["first_divergence"] == 4


def test_all_support_statuses_unknown_cascade_and_reset(client):
    examples = client.get("/api/typed").json()["examples"]
    assert {x["status"] for x in examples} == {
        "OBSERVED",
        "INFERRED_SUPPORTED",
        "AMBIGUOUS",
        "UNSUPPORTED",
    }
    for example in examples:
        output = client.post(
            "/api/typed/preview", headers=HEADERS, json={"requests": example["actions"]}
        ).json()
        assert output["oracle_actions"] == 0
        assert output["rows"][-1]["support"]["status"] == example["status"]
    unknown = next(x["actions"] for x in examples if x["status"] == "UNSUPPORTED")
    requests = [
        *unknown,
        {"operation": "get_balance", "arguments": {}},
        {"control": "reset"},
        {"operation": "get_balance", "arguments": {}},
    ]
    rows = client.post("/api/typed/preview", headers=HEADERS, json={"requests": requests}).json()[
        "rows"
    ]
    assert rows[-3]["state_after"] is None
    assert rows[-3]["output"]["bbt_unsupported"] is True
    assert rows[-2]["state_after"] == [0, False]
    assert not rows[-1]["output"].get("bbt_unsupported")
    observed = next(x for x in examples if x["status"] == "OBSERVED")
    row = client.post(
        "/api/typed/preview", headers=HEADERS, json={"requests": observed["actions"]}
    ).json()["rows"][-1]
    assert row["evidence"] and row["evidence"][0]["experiment"]


def test_twin_independent_with_no_oracle_or_package_in_working_directory(tmp_path):
    model = BehavioralModel.model_validate_json(
        (ROOT / "evidence/m3-demo/loop/revisions/001/model.json").read_text()
    )
    twin = tmp_path / "twin.py"
    generate_twin(model, twin)
    requests = [
        {"control": "reset"},
        *[{"operation": "advance", "arguments": {}}] * 4,
        {"operation": "commit", "arguments": {}},
    ]
    assert list(tmp_path.iterdir()) == [twin]
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(twin)],
        cwd=tmp_path,
        input="".join(json.dumps(r) + "\n" for r in requests),
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    outputs = [json.loads(line) for line in result.stdout.splitlines()]
    assert outputs[-1] == {"result": "accepted"}
    assert len(outputs) == len(requests)
    assert "subprocess" not in twin.read_text() and "socket" not in twin.read_text()


def test_events_paginate_without_mutation(client):
    path = ROOT / "evidence/m3-demo/loop/observations.sqlite"
    before = path.read_bytes()
    first = client.get("/api/experiments/m3-replay/events?offset=0&limit=3").json()
    second = client.get("/api/experiments/m3-replay/events?offset=3&limit=3").json()
    assert len(first["rows"]) == 3
    assert first["rows"][-1]["id"] < second["rows"][0]["id"]
    assert path.read_bytes() == before
    assert client.get("/api/experiments/m3-replay/events?limit=101").status_code == 422
    assert client.get("/api/experiments/m3-replay/events?offset=-1").status_code == 422


def test_benchmark_failures_and_empty_denominators_remain(client):
    data = client.get("/api/benchmarks").json()
    assert data["summary"]["cells"] == 216 and len(data["cells"]) == 324
    assert data["summary"]["unreached_cells"] == 138
    unsupported = [c for c in data["cells"] if c["status"] == "model_class_unsupported"]
    assert len(unsupported) == 24
    assert all(
        c["metrics"]["conditional_accuracy"] is None
        and c["metrics"]["prediction_coverage"] == 0
        and not c["criterion_reached"]
        for c in unsupported
    )


@pytest.mark.parametrize("endpoint", ["/api/demo", "/api/typed/preview"])
def test_cross_origin_and_missing_header_cannot_mutate(client, endpoint):
    assert client.post(endpoint, json={}).status_code == 403
    assert (
        client.post(
            endpoint, headers=HEADERS | {"Origin": "https://example.com"}, json={}
        ).status_code
        == 403
    )
    assert client.get("/api/experiments", headers={"Host": "evil.example"}).status_code == 400


def test_bounded_body_and_no_arbitrary_executables(client):
    assert (
        client.post("/api/demo", headers=HEADERS, json={"target": "arbitrary.py"}).status_code
        == 422
    )
    assert (
        client.post("/api/typed/preview", headers=HEADERS, json={"requests": [{}] * 31}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/typed/preview", headers=HEADERS, json={"requests": [{"x": "a" * 33000}]}
        ).status_code
        == 413
    )
    assert client.get("/api/experiments/unknown/export/0/twin").status_code == 404
    assert client.get("/api/experiments/m3-replay/export/100/twin").status_code == 404
    assert client.get("/api/experiments/m3-replay/export/0/secrets").status_code == 404


def test_corrupted_model_fails_integrity_without_changing_history(tmp_path, monkeypatch):
    source = ROOT / "evidence/m3-demo/loop"
    (tmp_path / "loop/revisions/000").mkdir(parents=True)
    (tmp_path / "loop/summary.json").write_bytes((source / "summary.json").read_bytes())
    (tmp_path / "loop/revisions/000/model.json").write_text("{}")
    evidence = Evidence(ROOT, tmp_path / "runs")
    monkeypatch.setattr(evidence, "folder", lambda _: tmp_path)
    with pytest.raises(ValueError, match="integrity"):
        evidence.model_path("m3-replay", 0)
    with pytest.raises(ValueError, match="leaves"):
        contained(tmp_path, "../outside")
    with pytest.raises(ValueError, match="historical"):
        create_app(ROOT, ROOT / "evidence/m7")


def test_job_failure_is_explicit_and_not_success(client, monkeypatch):
    from blackbox_twin import workbench

    def fail(*args):
        raise TimeoutError("owned process timeout (test injection)")

    monkeypatch.setattr(workbench, "run_demo", fail)
    response = client.post("/api/demo", headers=HEADERS, json={})
    assert response.status_code == 202
    name = response.json()["id"]
    for _ in range(100):
        state = client.get("/api/jobs/" + name).json()
        if state["status"] != "running":
            break
        time.sleep(0.01)
    assert state["status"] == "failed" and "timeout" in state["error"]
    assert not any(x["id"] == name for x in client.get("/api/experiments").json())


def test_one_worker_and_shutdown_waits_for_cleanup(tmp_path, monkeypatch):
    from blackbox_twin import workbench

    started, release, cleaned = threading.Event(), threading.Event(), threading.Event()

    def bounded(*args):
        started.set()
        try:
            release.wait(2)
            return {"status": "test double"}
        finally:
            cleaned.set()

    monkeypatch.setattr(workbench, "run_demo", bounded)
    with TestClient(create_app(ROOT, tmp_path / "runs")) as client:
        assert client.post("/api/demo", headers=HEADERS, json={}).status_code == 202
        assert started.wait(1)
        assert client.post("/api/demo", headers=HEADERS, json={}).status_code == 409
        release.set()
    assert cleaned.is_set()
    assert not any(t.name.startswith("bbt-owned-demo") for t in threading.enumerate())


def test_frontend_assets_served_locally(client):
    page = client.get("/")
    assert page.status_code == 200 and "/assets/app.js" in page.text
    assert "script-src 'self'" in page.headers["Content-Security-Policy"]
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/app.css").status_code == 200
