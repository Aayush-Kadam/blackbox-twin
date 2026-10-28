"""Independent non-editable reproduction of six preregistered representative cells."""

import argparse
import json
from importlib.metadata import distribution
from pathlib import Path

from blackbox_twin.benchmark import score_points, source_digest, train_cell
from blackbox_twin.cli import load_target

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--suite", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
config = json.loads((args.suite / "config.json").read_text())
assert source_digest() == config["source_sha256"]
protocol = config["protocol"]
seed = protocol["seeds"][2]
training_config = {
    k: protocol[k] for k in ("budgets", "max_resets", "seconds_per_run", "pool_size", "max_length")
}
args.out.mkdir(parents=True)
checks = []
for family in protocol["families"]:
    pair = args.suite / family / str(seed)
    target, script = load_target(pair / "target/target.json")
    reference = json.loads((pair / "evaluation/references.json").read_text())
    for method in ("cost-aware", "aalpy-random-w"):
        original = json.loads((pair / method / "result.json").read_text())
        folder = args.out / family / method
        result = train_cell(
            target,
            script,
            folder,
            training_config,
            method,
            protocol.get("selection_seed_offset", 0) + seed,
        )
        points = score_points(folder, result, reference)
        assert result["costs"]["actions"] == original["training"]["costs"]["actions"]
        assert result["costs"]["resets"] == original["training"]["costs"]["resets"]
        assert points == original["points"]
        assert result["counterexamples"] == original["training"]["counterexamples"]
        checks.append(
            {
                "family": family,
                "seed": seed,
                "method": method,
                "status": "PASS",
                "actions": result["costs"]["actions"],
                "resets": result["costs"]["resets"],
            }
        )
metadata = json.loads(distribution("blackbox-twin").read_text("direct_url.json"))
assert not metadata.get("dir_info", {}).get("editable", False)
report = {
    "reproduction": "PASS",
    "non_editable": True,
    "cells": checks,
    "matches": "physical counts, all checkpoint states/fidelities and counterexamples",
}
(args.out / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
