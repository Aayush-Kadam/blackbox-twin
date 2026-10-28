"""Inspectable pilot metrics; failures and unreached thresholds remain explicit."""

import csv
import json
import math
import statistics
from pathlib import Path


def aulc(points):
    area, previous_budget, previous_fidelity = 0.0, 0, 0.0
    for point in points:
        area += (point["ceiling"] - previous_budget) * previous_fidelity
        previous_budget, previous_fidelity = point["ceiling"], point["trace_fidelity"]
    return area / previous_budget if previous_budget else 0.0


def summarize(root: Path):
    config = json.loads((root / "config.json").read_text())["protocol"]
    rows = []
    for path in sorted(root.glob("*/*/*/result.json")):
        result = json.loads(path.read_text())
        points = result["points"]
        threshold = next((p["ceiling"] for p in points if p["trace_fidelity"] >= 0.95), None)
        rows.append(
            {
                "family": result["family"],
                "seed": result["seed"],
                "method": result["method"],
                "status": result["training"]["status"],
                "threshold_ceiling": threshold,
                "threshold_reached": threshold is not None,
                "aulc": aulc(points),
                "actions": result["training"]["costs"]["actions"],
                "resets": result["training"]["costs"]["resets"],
                "planner_seconds": result["training"]["planner_seconds"],
                "wall_seconds": result["training"]["wall_seconds"],
                "counterexamples": len(result["training"]["counterexamples"]),
                "points": points,
            }
        )
    aggregate, paired = {}, {}
    for method in config["methods"]:
        cells = [row for row in rows if row["method"] == method]
        reached = [row["threshold_ceiling"] for row in cells if row["threshold_reached"]]
        aggregate[method] = {
            "runs": len(cells),
            "threshold_reached": len(reached),
            "threshold_median_among_reached": statistics.median(reached) if reached else None,
            "median_aulc": statistics.median([r["aulc"] for r in cells]) if cells else None,
            "median_resets": statistics.median([r["resets"] for r in cells]) if cells else None,
            "total_actions": sum(r["actions"] for r in cells),
            "total_training_wall_seconds": sum(r["wall_seconds"] for r in cells),
            "total_planning_seconds": sum(r["planner_seconds"] for r in cells),
            "median_fidelity_by_ceiling": {
                str(b): statistics.median(
                    [p["trace_fidelity"] for r in cells for p in r["points"] if p["ceiling"] == b]
                )
                for b in config["budgets"]
            }
            if cells
            else {},
            "failures": [
                f"{r['family']}/{r['seed']}:{r['status']}"
                for r in cells
                if r["status"] not in {"budget_exhausted", "search_completed"}
            ],
        }
    for baseline in [m for m in config["methods"] if m != "cost-aware"]:
        differences, families = [], {}
        for row in [r for r in rows if r["method"] == "cost-aware"]:
            match = next(
                (
                    r
                    for r in rows
                    if r["method"] == baseline
                    and (r["family"], r["seed"]) == (row["family"], row["seed"])
                ),
                None,
            )
            if match:
                delta = row["aulc"] - match["aulc"]
                differences.append(delta)
                families.setdefault(row["family"], []).append(delta)
        paired[baseline] = {
            "median_aulc_difference": statistics.median(differences) if differences else None,
            "wins": sum(d > 1e-12 for d in differences),
            "ties": sum(abs(d) <= 1e-12 for d in differences),
            "losses": sum(d < -1e-12 for d in differences),
            "range": [min(differences), max(differences)] if differences else None,
            "by_family": {
                f: {
                    "median_difference": statistics.median(ds),
                    "wins": sum(d > 1e-12 for d in ds),
                    "pairs": len(ds),
                }
                for f, ds in families.items()
            },
        }
    supported_families = []
    for family in config["families"]:
        if all(
            paired.get(b, {}).get("by_family", {}).get(family, {}).get("wins", 0)
            >= math.ceil(0.8 * len(config["seeds"]))
            and paired[b]["by_family"][family]["median_difference"] > 0
            for b in ("aalpy-random-w", "aalpy-state-prefix")
        ):
            supported_families.append(family)
    expected = len(config["families"]) * len(config["seeds"]) * len(config["methods"])
    complete = len(rows) == expected and not any(a["failures"] for a in aggregate.values())
    verdict = (
        "INCONCLUSIVE"
        if not complete or len(config["seeds"]) < 5 or len(config["families"]) < 3
        else "SUPPORTED"
        if len(supported_families) == len(config["families"])
        else "PARTIALLY SUPPORTED"
        if supported_families
        else "NOT SUPPORTED"
    )
    reference_cost = {"actions": 0, "resets": 0}
    for path in root.glob("*/*/evaluation/references.json"):
        costs = json.loads(path.read_text())["costs"]
        for key in reference_cost:
            reference_cost[key] += costs[key]
    summary = {
        "schema_version": 1,
        "completed_cells": len(rows),
        "expected_cells": expected,
        "performance_hypothesis": verdict,
        "supported_families": supported_families,
        "methods": aggregate,
        "paired_cost_aware_minus_baseline": paired,
        "evaluation_reference_cost_shared_across_methods": reference_cost,
        "aulc_definition": "left-constant step integral from (0,0), divided by maximum ceiling",
        "threshold_definition": "first fixed checkpoint >=95%; null denotes unreached",
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    flat = []
    for row in rows:
        for point in row["points"]:
            flat.append({**{k: v for k, v in row.items() if k != "points"}, **point})
    if flat:
        with (root / "results.csv").open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(flat[0]))
            writer.writeheader()
            writer.writerows(flat)
    return summary
