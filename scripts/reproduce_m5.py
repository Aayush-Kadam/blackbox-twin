"""One non-editable installed learning reproduction and isolated dependency-free twin run."""

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

import blackbox_twin
from blackbox_twin.m5 import train


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True)
    distribution = importlib.metadata.distribution("blackbox-twin")
    direct = json.loads(distribution.read_text("direct_url.json"))
    assert not direct.get("dir_info", {}).get("editable", False)
    protocol = json.loads((args.suite / "protocol.json").read_text())
    pair = args.suite / "eval-a"
    result = train(protocol["contract"], pair / "oracle.py", args.out / "training", "adaptive")
    previous = json.loads((pair / "adaptive/training.json").read_text())
    assert result["status"] == previous["status"] == "completed"
    assert result["counterexamples"] == previous["counterexamples"]
    for kind in ("actions", "resets"):
        assert result["costs"][kind] == previous["costs"][kind]
    model = json.loads((args.out / "training" / result["model"]).read_text())
    old_model = json.loads((pair / "adaptive" / previous["model"]).read_text())
    assert model["states"] == old_model["states"] and model["rules"] == old_model["rules"]
    isolated = args.out / "isolated"
    isolated.mkdir()
    twin = isolated / "wallet_twin.py"
    shutil.copyfile(args.out / "training" / result["twin"], twin)
    cases = json.loads((pair / "evaluation-cases.json").read_text())
    truth = json.loads((pair / "evaluation-reference/references.json").read_text())["outputs"]
    requests, expected = [], []
    for case, outputs in zip(cases, truth, strict=True):
        requests.append({"control": "reset"})
        requests.extend(case["actions"])
        expected.append({"control": "reset", "ok": True})
        expected.extend(outputs)
    process = subprocess.run(
        [sys.executable, "-I", "-S", "-u", str(twin.resolve())],
        cwd=isolated,
        input="\n".join(map(json.dumps, requests)) + "\n",
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    outputs = [json.loads(line) for line in process.stdout.splitlines()]
    assert not process.stderr
    assert outputs == expected
    receipt = {
        "reproduction": "PASS",
        "installed_module": blackbox_twin.__file__,
        "non_editable": True,
        "training_costs": result["costs"],
        "rules_and_states_match": True,
        "isolated_cases": len(cases),
        "isolated_actions": sum(len(c["actions"]) for c in cases),
        "isolated_resets": len(cases),
        "isolated_exact": True,
        "scope": "one adaptive cell and its twin, not all four primary cells",
    }
    (args.out / "summary.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
