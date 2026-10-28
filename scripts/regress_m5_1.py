"""Replay historical B failures as labelled development regressions, never fresh holdout."""

import json
from collections import Counter
from pathlib import Path

from blackbox_twin.m5 import acquire_reference, write
from blackbox_twin.m51 import evaluate
from blackbox_twin.support import compile_support
from blackbox_twin.synthesis import generate_twin

ROOT = Path(__file__).resolve().parents[1]


def main():
    old = ROOT / "evidence/m5-primary/eval-b"
    out = ROOT / "evidence/m5-1-autopsy/policy-regressions"
    out.mkdir()
    receipt = json.loads((old / "adaptive/training.json").read_text())
    legacy = json.loads((old / "adaptive" / receipt["model"]).read_text())
    cases = json.loads((old / "evaluation-cases.json").read_text())
    history = json.loads((old / "evaluation-reference/references.json").read_text())["outputs"]
    original_predictions = json.loads((old / "evaluation-adaptive/references.json").read_text())[
        "outputs"
    ]
    pairs = [
        (i, c, history[i], original_predictions[i])
        for i, c in enumerate(cases)
        if c["category"] in {"unseen", "exhaustive"}
    ]
    subset = [c for _, c, _, _ in pairs]
    model = compile_support(
        legacy["contract"],
        legacy["observations"],
        [
            {
                "kind": "historical_development_only",
                "model": "m5-primary/eval-b/adaptive/revision-004",
            }
        ],
    )
    write(out / "model.json", model.model_dump())
    generate_twin(model, out / "twin.py")
    truth = acquire_reference(old / "oracle.py", model.contract, subset, out / "original-replay")
    assert truth == [expected for _, _, expected, _ in pairs]
    result = evaluate(
        out / "twin.py", model.model_dump(), model.contract, subset, truth, out / "twin-replay"
    )
    predictions = json.loads((out / "twin-replay/references.json").read_text())["outputs"]
    records = []
    for (index, case, expected, previous), actual in zip(pairs, predictions, strict=True):
        wrong_concrete = any(
            not a.get("bbt_unsupported") and a != b for a, b in zip(actual, expected, strict=True)
        )
        status = (
            "incorrect_prediction"
            if wrong_concrete
            else "explicit_abstention"
            if any(a.get("bbt_unsupported") for a in actual)
            else "correct_prediction"
        )
        records.append(
            {
                "original_case_index": index,
                "category": case["category"],
                "historical_exact": previous == expected,
                "new_status": status,
                "new_exact": actual == expected,
                "historical_target": expected,
                "historical_prediction": previous,
                "new_prediction": actual,
                "original_model": "m5-primary/eval-b/adaptive/revision-004/model.json",
            }
        )
    write(out / "regressions.json", records)
    write(
        out / "summary.json",
        {
            "label": "DEVELOPMENT ONLY",
            "metrics": result,
            "unseen_statuses": dict(
                Counter(r["new_status"] for r in records if r["category"] == "unseen")
            ),
            "exhaustive_statuses": dict(
                Counter(r["new_status"] for r in records if r["category"] == "exhaustive")
            ),
            "historical_failures_retained": sum(not r["historical_exact"] for r in records),
        },
    )
    print(json.dumps(json.loads((out / "summary.json").read_text()), indent=2))


if __name__ == "__main__":
    main()
