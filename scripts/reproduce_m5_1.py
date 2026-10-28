"""Non-editable installed training plus isolated plain/explained support-policy reproduction."""

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

import blackbox_twin
from blackbox_twin.m51 import train_hardened


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True)
    direct = json.loads(
        importlib.metadata.distribution("blackbox-twin").read_text("direct_url.json")
    )
    assert not direct.get("dir_info", {}).get("editable", False)
    protocol = json.loads((args.suite / "protocol.json").read_text())
    pair = args.suite / "fresh-0"
    receipt = train_hardened(
        protocol["contract"],
        pair / "oracle.py",
        args.out / "training",
        protocol["probe_seed"],
        protocol["max_probes"],
    )
    previous = json.loads((pair / "hardened/training.json").read_text())
    assert receipt["status"] == previous["status"] == "completed"
    assert receipt["model_id"] == previous["model_id"]
    for key in ("actions", "resets"):
        assert receipt["costs"][key] == previous["costs"][key]
    model = json.loads((args.out / "training" / receipt["model"]).read_text())
    old_model = json.loads((pair / "hardened" / previous["model"]).read_text())
    assert model["cells"] == old_model["cells"]
    assert receipt["regressions"] == previous["regressions"]
    isolated = args.out / "isolated"
    isolated.mkdir()
    script = isolated / "twin.py"
    shutil.copyfile(args.out / "training" / receipt["twin"], script)
    cases = json.loads((pair / "evaluation-cases.json").read_text())
    predictions = json.loads((pair / "evaluation-hardened/references.json").read_text())["outputs"]
    requests, expected = [], []
    for case, outputs in zip(cases, predictions, strict=True):
        requests.append({"control": "reset"})
        requests.extend(case["actions"])
        expected.append({"control": "reset", "ok": True})
        expected.extend(outputs)
    for explain in (False, True):
        command = [sys.executable, "-I", "-S", "-u", str(script.resolve())]
        if explain:
            command.append("--explain")
        process = subprocess.run(
            command,
            cwd=isolated,
            input="\n".join(map(json.dumps, requests)) + "\n",
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert not process.stderr
        actual = [json.loads(line) for line in process.stdout.splitlines()]
        assert ([row["output"] for row in actual] if explain else actual) == expected
        if explain:
            assert {row["support"]["status"] for row in actual} == {
                "OBSERVED",
                "INFERRED_SUPPORTED",
                "AMBIGUOUS",
                "UNSUPPORTED",
            }
    summary = {
        "reproduction": "PASS",
        "installed_module": blackbox_twin.__file__,
        "non_editable": True,
        "training_costs": receipt["costs"],
        "model_id": receipt["model_id"],
        "support_cells_identical": True,
        "isolated_cases_per_mode": len(cases),
        "isolated_actions_per_mode": sum(len(c["actions"]) for c in cases),
        "isolated_resets_per_mode": len(cases),
        "modes": ["plain", "explained"],
        "claim": "policy outputs reproduced including abstentions; not 100% target fidelity",
        "scope": "one hardened cell, not six-cell repetition",
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
