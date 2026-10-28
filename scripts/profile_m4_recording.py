"""Development-only profiling; both modes execute identical real physical actions."""

import argparse
import json
import time
from pathlib import Path

from blackbox_twin.benchmark import benchmark_recorder
from blackbox_twin.cli import load_target
from blackbox_twin.contracts import QueryBudget
from blackbox_twin.oracle import ProcessOracle, Session
from blackbox_twin.storage import Recorder

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True)
target, script = load_target(
    Path(__file__).resolve().parents[1] / "examples/order_processing/target.json"
)
rows = []
for mode in ("default-delete-full", "benchmark-wal-normal"):
    factory = Recorder if mode == "default-delete-full" else benchmark_recorder
    recorder = factory(args.out / f"{mode}.sqlite", {"mode": mode})
    oracle = ProcessOracle(script)
    session = Session(oracle, target, QueryBudget(), recorder, "development-profile")
    start = time.perf_counter()
    for _ in range(40):
        session.trace(["create", "authorize", "capture", "refund", "status"])
    rows.append(
        {
            "mode": mode,
            "costs": session.costs.model_dump(),
            "wall_seconds": time.perf_counter() - start,
        }
    )
    oracle.close()
    recorder.close("completed")
(args.out / "profile.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
