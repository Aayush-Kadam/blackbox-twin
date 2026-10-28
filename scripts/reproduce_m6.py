"""Small non-editable M6 reproduction; run after the frozen campaign completes."""

import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from blackbox_twin.contracts import Target
from blackbox_twin.m6_run import model_predictions, source_hashes
from blackbox_twin.m6_train import finite_train, typed_train


def read(path):
    return json.loads(path.read_text())


def run(root, out):
    out.mkdir(parents=True)
    protocol = read(root / "protocol.json")
    assert source_hashes() == protocol["source_sha256"]
    direct = json.loads(
        importlib.metadata.distribution("blackbox-twin").read_text("direct_url.json")
    )
    assert not direct.get("dir_info", {}).get("editable", False)
    results = read(root / "results.json")
    checks = []
    for target_id, method, ceiling in [
        ("A-easy-0", "aalpy-state-prefix", 1000),
        ("B-wallet-0", "hardened", 1500),
        ("C-inventory-0", "fixed-grid", 1500),
    ]:
        old = next(
            r
            for r in results
            if r["target"] == target_id
            and r["method"] == method
            and r["learner_index"] == 0
            and max(p["ceiling"] for p in r["points"]) == ceiling
        )
        target = root / target_id / "target"
        folder = out / target_id
        seeds = protocol["learner_seeds"][0], protocol["training_seeds"][0]
        if target_id.startswith("B"):
            receipt = typed_train(
                read(target / "public-contract.json"),
                target / "oracle.py",
                folder,
                ceiling,
                method,
                *seeds,
            )
        else:
            receipt = finite_train(
                Target.model_validate(read(target / "target.json")),
                target / "oracle.py",
                folder,
                [250, 1000] if target_id.startswith("A") else [1500],
                method,
                *seeds,
                concrete=target_id.startswith("C"),
            )
        assert receipt["status"] == old["training"]["status"]
        assert all(
            receipt["costs"][k] == old["training"]["costs"][k] for k in ("actions", "resets")
        )
        point = receipt["points"][-1]
        previous = old["points"][-1]
        model = read(folder / point["model"])
        old_model = read(root / old["training_folder"] / previous["model"])
        requests, expected = [], []
        for case in read(target / "inputs.json"):
            outputs = model_predictions(model, case["actions"])[0]
            assert outputs == model_predictions(old_model, case["actions"])[0]
            requests.extend([{"control": "reset"}, *case["actions"]])
            expected.extend([{"control": "reset", "ok": True}, *outputs])
        process = subprocess.run(
            [sys.executable, "-I", "-S", str((folder / point["twin"]).resolve())],
            input="".join(json.dumps(a) + "\n" for a in requests),
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
            cwd=folder,
        )
        assert [json.loads(line) for line in process.stdout.splitlines()] == expected
        checks.append(
            {
                "target": target_id,
                "method": method,
                "status": receipt["status"],
                "costs": receipt["costs"],
                "isolated_requests": len(requests),
                "prediction_policy_reproduced": True,
            }
        )
    report = {
        "verification": "PASS",
        "python": sys.version,
        "installation": direct,
        "checks": checks,
        "note": "Policy reproduction includes refusals; not perfect target fidelity.",
    }
    (out / "verification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.out.resolve())
