"""Reconcile M6 supported observations to physical database rows."""

import argparse
import json
from collections import Counter
from pathlib import Path

from audit_m5_1 import evidence_rows


def audit(root):
    results = json.loads((root / "results.json").read_text())
    counts, models, observations = Counter(), 0, 0
    for result in results:
        if result["track"] != "B" or result["method"] != "hardened":
            continue
        folder = root / result["training_folder"]
        evidence = evidence_rows(folder / "observations.sqlite")
        assert (
            result["training"]["regressions"]["tested"]
            == result["training"]["regressions"]["passed"]
        )
        for point in result["points"]:
            model = json.loads((folder / point["model"]).read_text())
            for row in model["observations"]:
                assert row["amount"] == row["action"]["arguments"].get("amount", 0)
                assert (
                    row["experiment"],
                    row["balance"],
                    row["frozen"],
                    json.dumps(row["action"], sort_keys=True),
                    json.dumps(row["output"], sort_keys=True),
                ) in evidence
                observations += 1
            counts.update(c["status"] for c in model["cells"].values())
            models += 1
    report = {
        "audit": "PASS",
        "models": models,
        "observations_reconciled": observations,
        "serialized_cell_status_counts": dict(counts),
        "scope": "Physical evidence and completed regressions; bounded version-space "
        "recompilation checked separately in audit.json.",
    }
    (root / "support-audit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    audit(parser.parse_args().root)
