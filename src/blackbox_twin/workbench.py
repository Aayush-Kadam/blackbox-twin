"""Local-only FastAPI transport for the M7 React evidence workbench.

Optional dependency: install blackbox-twin[workbench,workbench-test].
"""

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .local_boundary import LocalBoundary
from .m7_data import Evidence, read
from .m7_demo import run_demo
from .run_limits import storage_size


class Preview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: list[dict[str, JsonValue]] = Field(min_length=1, max_length=30)


class DemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Jobs:
    def __init__(self, project, runs, max_runs=3, max_storage_bytes=64 * 1024 * 1024):
        self.project, self.runs = project, runs
        self.max_runs, self.max_storage_bytes = max_runs, max_storage_bytes
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bbt-owned-demo")
        self.lock, self.jobs, self.closed = threading.Lock(), {}, False

    def start(self):
        with self.lock:
            if self.closed or any(j["status"] == "running" for j in self.jobs.values()):
                raise HTTPException(
                    409, "A bounded demonstration is already running or shutting down"
                )
            prior = {p.name for p in self.runs.glob("live-*")} | set(self.jobs)
            if len(prior) >= self.max_runs:
                raise HTTPException(
                    429, "Demo count limit reached; choose a new output root explicitly"
                )
            if storage_size(self.runs) >= self.max_storage_bytes:
                raise HTTPException(429, "Demo output storage admission limit reached")
            name = "live-" + uuid4().hex
            self.jobs[name] = {"id": name, "status": "running", "stage": "starting"}
            self.pool.submit(self._run, name)
            return dict(self.jobs[name])

    def _run(self, name):
        try:
            receipt = run_demo(self.project, self.runs / name)
            result = {"id": name, "status": "completed", "receipt": receipt}
        except Exception as exc:
            result = {
                "id": name,
                "status": "failed",
                "error": "Demonstration failed: " + type(exc).__name__.lower(),
                "note": "Inspect local progress.json for details. Partial evidence is retained.",
            }
        with self.lock:
            self.jobs[name] = result

    def get(self, name):
        with self.lock:
            if name not in self.jobs:
                raise HTTPException(404, "Unknown demonstration job")
            result = dict(self.jobs[name])
        path = self.runs / name / "progress.json"
        if result["status"] == "running" and path.exists():
            try:
                result["stage"] = read(path).get("stage", "running")
            except (OSError, json.JSONDecodeError):
                pass
        return result

    def close(self):
        with self.lock:
            self.closed = True
        # Existing oracle/session timeouts bound work. Do not kill a worker and orphan its child.
        self.pool.shutdown(wait=True, cancel_futures=True)


def create_app(project: Path, runs: Path, *, max_runs=3):
    project, runs = project.resolve(), runs.resolve()
    if runs == project or runs.is_relative_to(project / "evidence"):
        raise ValueError("Live demo outputs must not overwrite historical evidence")
    evidence, jobs = Evidence(project, runs), Jobs(project, runs, max_runs=max_runs)

    @asynccontextmanager
    async def lifespan(app):
        yield
        jobs.close()

    app = FastAPI(
        title="BlackBox Twin · local scientific workbench",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    app.state.jobs, app.state.evidence = jobs, evidence
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    app.add_middleware(LocalBoundary)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse(
            {"detail": "Unknown allowlisted experiment or artifact"}, status_code=404
        )

    @app.exception_handler(FileNotFoundError)
    async def unavailable(request, exc):
        return JSONResponse(
            {"detail": "Required evidence unavailable; inspect the local project."}, status_code=409
        )

    @app.exception_handler(ValueError)
    async def integrity(request, exc):
        return JSONResponse(
            {"detail": "Evidence validation or integrity check failed"}, status_code=409
        )

    @app.get("/api/limits")
    def limits():
        return {
            "max_demo_runs_per_output_root": jobs.max_runs,
            "storage_admission_bytes": jobs.max_storage_bytes,
            "scope": "Admission checks, not a hard OS disk/memory quota",
        }

    @app.get("/api/experiments")
    def experiments():
        return evidence.experiments()

    @app.get("/api/experiments/{experiment}")
    def experiment(experiment: str):
        return evidence.detail(experiment)

    @app.get("/api/experiments/{experiment}/events")
    def events(experiment: str, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
        return evidence.events(experiment, offset, limit)

    @app.get("/api/experiments/{experiment}/export/{revision}/{kind}")
    def export(experiment: str, revision: int, kind: str):
        if kind not in {"model", "twin"}:
            raise HTTPException(404, "Export only supports validated model JSON or generated twin")
        path = evidence.model_path(experiment, revision, kind)
        return FileResponse(
            path,
            filename=f"bbt-revision-{revision}-" + path.name,
            media_type="application/json" if kind == "model" else "text/x-python",
        )

    @app.get("/api/typed")
    def typed():
        return evidence.typed()

    @app.post("/api/typed/preview")
    def preview(body: Preview):
        return evidence.preview(body.requests)

    @app.get("/api/benchmarks")
    def benchmarks():
        return evidence.benchmarks()

    @app.post("/api/demo", status_code=202)
    def demo(body: DemoRequest):
        return jobs.start()

    @app.get("/api/jobs/{name}")
    def job(name: str):
        return jobs.get(name)

    assets = Path(__file__).parent / "workbench_assets"

    @app.get("/")
    def index():
        return FileResponse(assets / "index.html")

    app.mount("/assets", StaticFiles(directory=assets, check_dir=False), name="assets")
    return app


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a local unprivileged port in 1024..65535")
    uvicorn.run(
        create_app(args.project, args.runs),
        host="127.0.0.1",
        port=args.port,
        timeout_graceful_shutdown=200,
        limit_concurrency=16,
        backlog=16,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
