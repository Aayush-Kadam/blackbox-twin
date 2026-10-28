"""Classify all historical B unseen traces from immutable independently executed evidence."""

import json
from collections import Counter
from pathlib import Path

from blackbox_twin.typed_runtime import guarded_step, predicate_matches

ROOT = Path(__file__).resolve().parents[1]
PAIR = ROOT / "evidence/m5-primary/eval-b"
OUT = ROOT / "evidence/m5-1-autopsy"


def main():
    OUT.mkdir()
    training = json.loads((PAIR / "adaptive/training.json").read_text())
    model = json.loads((PAIR / "adaptive" / training["model"]).read_text())
    cases = json.loads((PAIR / "evaluation-cases.json").read_text())
    truth = json.loads((PAIR / "evaluation-reference/references.json").read_text())["outputs"]
    measured = json.loads((PAIR / "evaluation-adaptive/references.json").read_text())["outputs"]
    inventory = []
    for index, (case, target, twin) in enumerate(zip(cases, truth, measured, strict=True)):
        if case["category"] != "unseen":
            continue
        state, first, explanations = (0, False), None, []
        for step, action in enumerate(case["actions"]):
            before = state
            state, predicted = guarded_step(model, state, action)
            assert predicted == twin[step]
            observed = [
                i
                for i, r in enumerate(model["observations"])
                if before is not None
                and (r["balance"], r["frozen"]) == before
                and r["action"] == action
            ]
            matching = [
                i
                for i, r in enumerate(model["rules"])
                if before is not None
                and r["operation"] == action["operation"]
                and r["frozen_context"] is before[1]
                and all(
                    predicate_matches(p, before[0], action["arguments"].get("amount", 0))
                    for p in r["guard"]
                )
            ]
            support = (
                "OBSERVED"
                if observed
                else "INFERRED"
                if not predicted.get("bbt_unsupported")
                else "UNSUPPORTED"
            )
            explanation = {
                "step": step,
                "action": action,
                "state_before": before,
                "state_after": state,
                "target": target[step],
                "twin": predicted,
                "support": support,
                "observation_indices": observed,
                "responsible_rules": [
                    {
                        "rule_index": i,
                        "guard": model["rules"][i]["guard"],
                        "updates": model["rules"][i]["updates"],
                        "evidence": model["rules"][i]["evidence"],
                    }
                    for i in matching
                ],
            }
            explanations.append(explanation)
            if predicted != target[step] and first is None:
                first = explanation
        if first:
            reason = first["twin"].get("reason")
            category = (
                "overlapping_selected_guards"
                if len(first["responsible_rules"]) > 1
                else "uncovered_selected_guards"
                if reason == "ambiguous_or_uncovered_guard"
                else "ambiguous_arithmetic_update"
                if reason == "ambiguous_update"
                else "other_requires_review"
            )
            prior = (
                (0, False)
                if first["step"] == 0
                else (target[first["step"] - 1]["balance"], target[first["step"] - 1]["frozen"])
            )
            first["state_matches_target_before_divergence"] = tuple(first["state_before"]) == prior
            first["state_is_observed"] = list(first["state_before"]) in model["states"]
        else:
            category = "exact_match"
        inventory.append(
            {
                "case_index": index,
                "exact_match": target == twin,
                "classification": category,
                "first_divergence": first,
                "actions": case["actions"],
                "steps": explanations,
                "original_model": "m5-primary/eval-b/adaptive/revision-004/model.json",
            }
        )
    summary = {
        "traces": len(inventory),
        "exact": sum(i["exact_match"] for i in inventory),
        "categories": dict(Counter(i["classification"] for i in inventory)),
        "first_failure_states_all_observed_and_correct": all(
            i["first_divergence"]["state_is_observed"]
            and i["first_divergence"]["state_matches_target_before_divergence"]
            for i in inventory
            if i["first_divergence"]
        ),
        "use": "DEVELOPMENT DIAGNOSIS ONLY; not untouched evaluation",
    }
    (OUT / "inventory.json").write_text(json.dumps(inventory, indent=2))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
