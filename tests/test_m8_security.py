"""M8 local-boundary and trusted-fixture hardening regressions."""

import asyncio
import json
import os
import subprocess
import threading
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from blackbox_twin.contracts import Action  # noqa: E402
from blackbox_twin.local_boundary import LocalBoundary  # noqa: E402
from blackbox_twin.m7_data import Evidence  # noqa: E402
from blackbox_twin.m7_demo import run_demo  # noqa: E402
from blackbox_twin.oracle import ProcessOracle, oracle_environment  # noqa: E402
from blackbox_twin.run_limits import storage_size  # noqa: E402
from blackbox_twin.workbench import Jobs, create_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def link_directory(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise

        def quote(p):
            return "'" + str(p).replace("'", "''") + "'"

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(target)}",
            ],
            capture_output=True,
            timeout=15,
        )
        if result.returncode:
            if os.environ.get("BBT_REQUIRE_PHYSICAL_LINKS") == "1":
                pytest.fail("Required physical link/junction creation was denied by the runner")
            pytest.skip("OS did not permit creation of an owned test link/junction")


@pytest.mark.parametrize(
    "host",
    [
        "localhost/a",
        "localhost?x=",
        "localhost#x",
        "localhost:0",
        "localhost:65536",
        "evil.example",
        "localhost\\x",
    ],
)
def test_malformed_host_rejected_before_url_reconstruction(tmp_path, host):
    with TestClient(create_app(ROOT, tmp_path / "runs")) as client:
        response = client.get("/api/limits", headers={"Host": host})
        assert response.status_code == 400
        assert "Content-Security-Policy" in response.headers


def test_duplicate_host_and_methods_rejected(tmp_path):
    with TestClient(create_app(ROOT, tmp_path / "runs")) as client:
        assert (
            client.get(
                "/api/limits", headers=[("Host", "localhost"), ("Host", "evil.example")]
            ).status_code
            == 400
        )
        assert client.delete("/api/demo", headers={"X-BBT-Local": "1"}).status_code == 405
        assert (
            client.post(
                "/api/demo", headers={"X-BBT-Local": "1", "Origin": "null"}, json={}
            ).status_code
            == 403
        )


async def boundary_case(body, declared, delay=0, seconds=0.05):
    called, sent = [], []

    async def app(scope, receive, send):
        called.append(await receive())

    async def receive():
        await asyncio.sleep(delay)
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    headers = [(b"host", b"localhost"), (b"x-bbt-local", b"1")]
    if declared is not None:
        headers.append((b"content-length", declared))
    await LocalBoundary(app, body_seconds=seconds)(
        {"type": "http", "method": "POST", "headers": headers}, receive, send
    )
    return called, sent


@pytest.mark.parametrize(
    "body,declared,status",
    [
        (b"x" * 32769, b"1", 413),
        (b"{}", b"1", 400),
        (b"{}", None, 411),
        (b"{}", b"-1", 411),
        (b"{}", b"999999", 413),
    ],
    ids=[
        "oversize-stream",
        "length-mismatch",
        "missing-length",
        "negative-length",
        "oversize-header",
    ],
)
def test_streaming_body_limits_do_not_trust_only_content_length(body, declared, status):
    called, sent = asyncio.run(boundary_case(body, declared))
    assert not called and sent[0]["status"] == status


def test_slow_request_body_has_a_deadline():
    called, sent = asyncio.run(boundary_case(b"{}", b"2", delay=0.1, seconds=0.01))
    assert not called and sent[0]["status"] == 408


@pytest.mark.parametrize(
    "body",
    [b"{", b'{"value":NaN}', b"\xff", b"[" * 2000 + b"]" * 2000],
    ids=["invalid", "nonstandard-constant", "invalid-unicode", "deep-nesting"],
)
def test_malformed_json_is_rejected_before_endpoint(body):
    called, sent = asyncio.run(boundary_case(body, str(len(body)).encode()))
    assert not called and sent[0]["status"] == 400


@pytest.mark.parametrize("name", ["../outside", "/outside", "a/../../outside"])
def test_resolved_traversal_rejected(tmp_path, name):
    from blackbox_twin.m7_data import contained

    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(ValueError, match="leaves"):
        contained(root, name)


def test_invalid_payloads_and_cors(tmp_path):
    with TestClient(create_app(ROOT, tmp_path / "runs")) as client:
        for payload in ({"requests": []}, {"requests": [{}] * 31}, {"other": True}):
            response = client.post("/api/typed/preview", headers={"X-BBT-Local": "1"}, json=payload)
            assert response.status_code == 422
            assert "access-control-allow-origin" not in response.headers
        response = client.post(
            "/api/demo",
            headers={"X-BBT-Local": "1", "Content-Type": "text/plain"},
            content="{}",
            follow_redirects=False,
        )
        assert response.status_code == 422


def test_subprocess_does_not_inherit_secret_or_python_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("BBT_TEST_SECRET", "synthetic-test-value")
    monkeypatch.setenv("PYTHONPATH", "synthetic-import-path")
    script = tmp_path / "owned-env-probe.py"
    script.write_text(
        "import json,os,sys\nfor line in sys.stdin:\n"
        " print(json.dumps({'secret_present':'BBT_TEST_SECRET' in os.environ,"
        "'pythonpath_present':'PYTHONPATH' in os.environ}),flush=True)\n",
        encoding="utf-8",
    )
    assert "BBT_TEST_SECRET" not in oracle_environment()
    oracle = ProcessOracle(script, scratch_root=tmp_path / "scratch")
    try:
        assert oracle.step(Action(operation="check")).payload == {
            "secret_present": False,
            "pythonpath_present": False,
        }
    finally:
        oracle.close()
    assert not list((tmp_path / "scratch").iterdir())


def test_historical_folder_link_escape_is_rejected(tmp_path):
    project, outside = tmp_path / "project", tmp_path / "outside"
    (project / "evidence").mkdir(parents=True)
    outside.mkdir()
    link_directory(project / "evidence/m3-demo", outside)
    evidence = Evidence(project, tmp_path / "runs")
    with pytest.raises(ValueError, match="leaves"):
        evidence.folder("m3-replay")


def test_nested_loop_link_escape_is_rejected(tmp_path):
    project, outside = tmp_path / "project", tmp_path / "outside"
    folder = project / "evidence/m3-demo"
    folder.mkdir(parents=True)
    outside.mkdir()
    (outside / "summary.json").write_text("{}")
    link_directory(folder / "loop", outside)
    with pytest.raises(ValueError, match="leaves"):
        Evidence(project, tmp_path / "runs").detail("m3-replay")


def test_allowed_fixture_name_cannot_link_to_an_outside_executable(tmp_path):
    project, outside = tmp_path / "project", tmp_path / "outside"
    (project / "examples/delayed").mkdir(parents=True)
    (project / "fixtures").mkdir()
    outside.mkdir()
    (outside / "delayed_process.py").write_text("raise RuntimeError('must not execute')")
    link_directory(project / "fixtures/targets", outside)
    (project / "examples/delayed/target.json").write_bytes(
        (ROOT / "examples/delayed/target.json").read_bytes()
    )
    with pytest.raises(ValueError, match="allowlist"):
        run_demo(project, tmp_path / "new-output")
    assert json.loads((tmp_path / "new-output/progress.json").read_text())["stage"] == "failed"


def test_output_storage_rejects_links_and_is_bounded(tmp_path):
    root, outside = tmp_path / "runs", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link_directory(root / "linked", outside)
    with pytest.raises(ValueError, match="Linked"):
        storage_size(root)
    with pytest.raises(ValueError, match="too many"):
        storage_size(outside, max_files=0)


def test_demo_admission_count_survives_server_restart(tmp_path):
    runs = tmp_path / "runs"
    (runs / ("live-" + "a" * 32)).mkdir(parents=True)
    jobs = Jobs(ROOT, runs, max_runs=1)
    try:
        with pytest.raises(Exception) as failure:
            jobs.start()
        assert failure.value.status_code == 429
    finally:
        jobs.close()


def test_storage_admission_limit_blocks_new_job(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "owned.bin").write_bytes(b"12345")
    jobs = Jobs(ROOT, runs, max_storage_bytes=4)
    try:
        with pytest.raises(Exception) as failure:
            jobs.start()
        assert failure.value.status_code == 429
    finally:
        jobs.close()


def test_error_details_do_not_disclose_local_paths(tmp_path, monkeypatch):
    from blackbox_twin import workbench

    finished = threading.Event()

    def fail(*args):
        finished.set()
        raise PermissionError("SYNTHETIC_PRIVATE_PATH_DO_NOT_DISPLAY")

    monkeypatch.setattr(workbench, "run_demo", fail)
    with TestClient(create_app(ROOT, tmp_path / "runs")) as client:
        job = client.post("/api/demo", headers={"X-BBT-Local": "1"}, json={}).json()
        assert finished.wait(1)
    state = client.app.state.jobs.get(job["id"])
    assert state["status"] == "failed"
    assert "SYNTHETIC_PRIVATE_PATH" not in json.dumps(state)
