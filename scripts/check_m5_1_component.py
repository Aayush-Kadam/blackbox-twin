"""Post-hoc component check: conservative policy before resolution, no new oracle calls."""

import json
from pathlib import Path

from blackbox_twin.m5 import write
from blackbox_twin.m51 import evaluate

ROOT = Path(__file__).resolve().parents[1]


def main():
    suite = ROOT / "evidence/m5-1-fresh"
    out = ROOT / "evidence/m5-1-component-check"
    out.mkdir()
    summary = {
        "label": "POST-HOC COMPONENT DIAGNOSTIC; no independent performance claim",
        "cases": {},
    }
    for name in ("fresh-0", "fresh-1"):
        pair = suite / name
        model = json.loads((pair / "hardened/revision-000/model.json").read_text())
        cases = json.loads((pair / "evaluation-cases.json").read_text())
        truth = json.loads((pair / "evaluation-reference/references.json").read_text())["outputs"]
        summary["cases"][name] = evaluate(
            pair / "hardened/revision-000/twin.py",
            model,
            model["contract"],
            cases,
            truth,
            out / name,
        )
    write(out / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
