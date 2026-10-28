import ast
import json
import sqlite3
from collections import deque
from pathlib import Path

from blackbox_twin.contracts import BehavioralModel

root = Path(__file__).resolve().parents[1]
out = root / "evidence/m4-1"
results = {}
for method in ["no-coverage", "no-suffix"]:
    changed, comparisons = 0, []
    for folder in sorted((root / "evidence/m4-confirmatory").glob("*/20[1-5]")):
        words = []
        for m in ["cost-aware", method]:
            with sqlite3.connect(
                f"file:{(folder / m / 'attempt-000/observations.sqlite').as_posix()}?mode=ro",
                uri=True,
            ) as db:
                words.append(
                    [
                        json.loads(r[0])["actions"]
                        for r in db.execute(
                            "SELECT content FROM artifacts WHERE kind='planner_decision' "
                            "ORDER BY rowid"
                        )
                    ]
                )
        same = words[0] == words[1]
        changed += not same
        comparisons.append(
            {
                "pair": folder.relative_to(root).as_posix(),
                "identical_decision_lists": same,
                "full_decisions": len(words[0]),
                "ablated_decisions": len(words[1]),
            }
        )
    results[method] = {"changed_decision_lists": changed, "comparisons": comparisons}
logs = []
for file in out.glob("*/diagnostics.json"):
    data = json.loads(file.read_text())
    records = data["records"]
    if not records:
        continue
    selected = [r for r in records if r["selected"]]
    assert data["dropped"] == 0
    assert all(
        r["actual_actions"] == len(r["selected"]) and r["actual_resets"] == 1 for r in selected
    )
    logs.append(
        {
            "cell": file.parent.name,
            "records": len(records),
            "selected": len(selected),
            "nonzero_coverage_candidate_instances": sum(r["coverage_nonzero"] for r in records),
            "nonzero_separator_candidate_instances": sum(r["separator_nonzero"] for r in records),
            "lengths_selected": sorted(set(len(r["selected"]) for r in selected)),
            "candidate_costs_match_actual": True,
        }
    )
dev = json.loads((out / "development.json").read_text())
profiles = json.loads((out / "profiles.json").read_text())
smokes = [
    json.loads((out / p / "summary.json").read_text())
    for p in ["default-cli-smoke", "default-cli-finite-smoke"]
]
abort = json.loads(
    (root / "evidence/m4-1-instrumentation-abort/random-301-cost-aware/training.json").read_text()
)
summary = {
    "ablation_decisions": results,
    "diagnostic_integrity": logs,
    "diagnostic_and_profile_actions": sum(d["costs"]["actions"] for d in dev)
    + sum(p["training"]["costs"]["actions"] for p in profiles.values()),
    "diagnostic_and_profile_resets": sum(d["costs"]["resets"] for d in dev)
    + sum(p["training"]["costs"]["resets"] for p in profiles.values()),
    "aborted_instrumentation_costs": abort["costs"],
    "cli_smoke_costs": [s["physical_costs"] for s in smokes],
    "all_non_test_original_actions": sum(d["costs"]["actions"] for d in dev)
    + sum(p["training"]["costs"]["actions"] for p in profiles.values())
    + abort["costs"]["actions"]
    + sum(s["physical_costs"]["actions"] for s in smokes),
    "all_non_test_original_resets": sum(d["costs"]["resets"] for d in dev)
    + sum(p["training"]["costs"]["resets"] for p in profiles.values())
    + abort["costs"]["resets"]
    + sum(s["physical_costs"]["resets"] for s in smokes),
}
exact_checks = []
sql_checked = 0
for receipt in out.glob("*/training.json"):
    recorded = json.loads(receipt.read_text())
    database = receipt.parent / "observations.sqlite"
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        counts = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
    assert recorded["costs"]["actions"] == counts.get("action", 0)
    assert recorded["costs"]["resets"] == counts.get("reset", 0)
    assert recorded["costs"]["actions"] <= 500
    sql_checked += 1
assert sql_checked == 13
summary["development_sql_receipts_checked"] = sql_checked
for cell in dev:
    fixture, method = cell["fixture"], cell["method"]
    target_folder = "target-rare-access" if fixture == "rare-access" else f"target-{fixture}"
    tree = ast.parse((out / target_folder / "oracle.py").read_text())
    # Independent evaluator only, after all training has finished.
    assignment = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "TABLE" for t in n.targets)
    )
    table = json.loads(ast.literal_eval(assignment.value.args[0]))
    model = BehavioralModel.model_validate_json(
        (out / f"{fixture}-{method}" / "latest-model.json").read_text()
    )
    queue = deque([(0, model.initial_state, ())])
    seen = {(0, model.initial_state)}
    mismatch = None
    while queue and mismatch is None:
        actual, inferred, prefix = queue.popleft()
        for symbol in model.actions:
            successor, output = table[actual][symbol]
            edge = model.transitions[inferred][symbol]
            word = prefix + (symbol,)
            if edge.output.payload != output:
                mismatch = word
                break
            pair = successor, edge.next_state
            if pair not in seen:
                seen.add(pair)
                queue.append((*pair, word))
    exact_checks.append(
        {
            "fixture": fixture,
            "method": method,
            "finite_product_agreement": mismatch is None,
            "shortest_mismatch": mismatch,
        }
    )
summary["post_training_evaluator_finite_product_checks"] = exact_checks
(out / "forensic-summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
