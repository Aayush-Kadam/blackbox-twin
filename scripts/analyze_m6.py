"""Derive descriptive M6 tables without selecting or changing training parameters."""

import argparse
import csv
import json
import statistics
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def analyze(root):
    results = read(root / "results.json")
    rows, guards, criterion = [], [], []
    for result in results:
        cases = read(root / result["target"] / "target/inputs.json")
        truth = read(root / result["reference_folder"] / "receipt.json")["outputs"]
        for point in result["points"]:
            base = {k: result[k] for k in ("target", "track", "family", "method", "learner_index")}
            base.update(
                ceiling=point["ceiling"],
                actual_actions=point["actual_actions"],
                total_run_actions=result["training"]["costs"]["actions"],
                resets=result["training"]["costs"]["resets"],
                wall_seconds=result["training"]["wall_seconds"],
                status=result["training"]["status"],
                model_bytes=point["model_bytes"],
                criterion_reached=point["criterion_reached"],
            )
            rows.append({**base, "stratum": "overall", **point["metrics"]["overall"]})
            for label, values in point["metrics"]["groups"].items():
                rows.append({**base, "stratum": label, **values})
            if result["track"] in {"B", "C"}:
                predicted = read(root / point["evaluation_folder"] / "receipt.json")["outputs"]
                tp = fp = fn = tn = refused = 0
                for case, original, twin in zip(cases, truth, predicted, strict=True):
                    if case["category"] != "exhaustive":
                        continue
                    index = case["probe_index"]
                    yes, claimed = (
                        original[index].get("status") == "ok",
                        twin[index].get("status") == "ok",
                    )
                    refused += bool(twin[index].get("bbt_unsupported"))
                    tp += yes and claimed
                    fp += not yes and claimed
                    fn += yes and not claimed
                    tn += not yes and not claimed
                guards.append(
                    {
                        **base,
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "tn": tn,
                        "refused": refused,
                        "acceptance_precision": tp / (tp + fp) if tp + fp else None,
                        "acceptance_recall": tp / (tp + fn) if tp + fn else None,
                    }
                )
                checked = guards[-1]
                assert point["metrics"]["guard_population"] == tp + fp + fn + tn
                assert point["metrics"]["guard_precision"] == checked["acceptance_precision"]
                assert point["metrics"]["guard_recall"] == checked["acceptance_recall"]
        first = next((p for p in result["points"] if p["criterion_reached"]), None)
        criterion.append(
            {k: result[k] for k in ("target", "method", "learner_index")}
            | {
                "first_ceiling": first["ceiling"] if first else None,
                "actual_actions_at_checkpoint": first["actual_actions"] if first else None,
            }
        )
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (root / "metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    grouped = {}
    metrics = (
        "trace_fidelity",
        "output_fidelity",
        "prediction_coverage",
        "conditional_accuracy",
        "false_supported_rate",
        "abstention_rate",
    )
    for row in rows:
        key = (row["track"], row["family"], row["method"], row["ceiling"], row["stratum"])
        grouped.setdefault(key, {}).setdefault(row["target"], []).append(row)
    aggregates = []
    for key, targets in sorted(grouped.items()):
        values = {}
        for metric in metrics:
            means = [
                statistics.mean(r[metric] for r in runs if r[metric] is not None)
                for runs in targets.values()
                if any(r[metric] is not None for r in runs)
            ]
            values[metric] = {
                "median_target_mean": statistics.median(means) if means else None,
                "range": [min(means), max(means)] if means else None,
            }
        aggregates.append(
            dict(zip(("track", "family", "method", "ceiling", "stratum"), key, strict=True))
            | {"targets": len(targets), "metrics": values}
        )
    report = {
        "aggregates": aggregates,
        "guard_acceptance_population": (
            "All evaluator-reachable contexts x two integer operations x integers -8..8; "
            "refusals count as no positive acceptance claim, not correct error reconstruction."
        ),
        "guard_acceptance": guards,
        "criterion_costs": criterion,
        "distinct_evaluation_sequences": sum(
            len(read(root / spec["id"] / "target/inputs.json"))
            for spec in read(root / "protocol.json")["targets"]
        ),
        "scored_trace_executions": sum(r["traces"] for r in rows if r["stratum"] == "overall"),
        "training_wall_seconds_sum": sum(r["training"]["wall_seconds"] for r in results),
    }
    (root / "analysis.json").write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in {"aggregates", "guard_acceptance", "criterion_costs"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    analyze(parser.parse_args().root)
