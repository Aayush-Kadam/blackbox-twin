"""Supplemental non-oracle path and aborted-job checks; no physical link substitution."""

import argparse
import json
import threading
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from blackbox_twin.m7_data import contained
from blackbox_twin.oracle import oracle_environment
from blackbox_twin.workbench import Jobs, create_app


def run(project, out):
    out.mkdir(parents=True)
    root = out / "owned-project"
    root.mkdir()
    outside = out / "owned-outside.txt"
    outside.write_text("public synthetic marker", encoding="utf-8")
    rejected = []
    for name in (str(outside.resolve()), "../owned-outside.txt", "a/../../owned-outside.txt"):
        try:
            contained(root, name)
        except ValueError:
            rejected.append(name)
    assert len(rejected) == 3
    responses = {}
    with TestClient(create_app(project, out / "unused-server-runs")) as client:
        for path in (
            "/api/experiments/%2e%2e%2fowned-outside.txt",
            "/api/experiments/%252e%252e%252fowned-outside.txt",
            "/api/experiments/C:%5coutside",
            "/api/experiments/m3-replay/export/0/%2e%2e",
        ):
            response = client.get(path)
            assert response.status_code in {404, 409}
            assert outside.read_text() not in response.text
            responses[path] = response.status_code
    completed = threading.Event()

    def abort(*args):
        completed.set()
        raise RuntimeError("owned synthetic abort")

    jobs = Jobs(project, out / "aborted-runs", max_runs=2)
    with patch("blackbox_twin.workbench.run_demo", abort):
        first = jobs.start()
        assert completed.wait(2)
        jobs.pool.shutdown(wait=True)
    assert jobs.get(first["id"])["status"] == "failed"
    # A fresh executor is a deliberate server restart; failed jobs do not hold the worker.
    restarted = Jobs(project, out / "aborted-runs", max_runs=2)
    with patch("blackbox_twin.workbench.run_demo", lambda *args: {"synthetic": True}):
        second = restarted.start()
        restarted.close()
    assert restarted.get(second["id"])["status"] == "completed"
    jobs.close()
    assert set(oracle_environment()) <= {
        "SystemRoot",
        "WINDIR",
        "PATH",
        "TEMP",
        "TMP",
        "LANG",
        "LC_ALL",
        "TZ",
    }
    report = {
        "status": "PASS",
        "outside_paths_rejected": len(rejected),
        "encoded_paths": responses,
        "aborted_job_restart": "PASS",
        "environment_keys_allowlisted": True,
        "scope": "Supplemental checks; four physical link cases remain unverified.",
    }
    (out / "checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.out.resolve())
