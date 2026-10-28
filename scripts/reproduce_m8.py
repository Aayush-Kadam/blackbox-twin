"""Non-editable wheel reproduction using only a declared data kit and installed package."""

import argparse
import importlib.metadata as metadata
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import blackbox_twin
from blackbox_twin.m6_train import unsupported_train
from blackbox_twin.m7_data import read, sha
from blackbox_twin.m7_demo import run_demo
from blackbox_twin.workbench import create_app


def run(kit, out):
    module = Path(blackbox_twin.__file__).resolve()
    assert module.is_relative_to(Path(sys.prefix).resolve())
    direct = metadata.distribution("blackbox-twin").read_text("direct_url.json")
    assert not json.loads(direct or "{}").get("dir_info", {}).get("editable", False)
    manifest = read(kit / "kit-manifest.json")
    for name, digest in manifest["files_sha256"].items():
        assert sha(kit / name) == digest
    receipt = run_demo(kit, out)
    assert receipt["scores"]["initial"] != receipt["scores"]["refined"]
    with TestClient(create_app(kit, out / "unused-runs")) as client:
        assert client.get("/").status_code == 200
        assert client.get("/assets/app.js").status_code == 200
        assert len(client.get("/api/benchmarks").json()["cells"]) == 324
        typed = client.get("/api/typed").json()
        assert {e["status"] for e in typed["examples"]} == {
            "OBSERVED",
            "INFERRED_SUPPORTED",
            "AMBIGUOUS",
            "UNSUPPORTED",
        }
        for example in typed["examples"]:
            response = client.post(
                "/api/typed/preview",
                headers={"X-BBT-Local": "1"},
                json={"requests": example["actions"]},
            )
            assert response.status_code == 200
    unsupported = unsupported_train(out / "inventory-unsupported", 100, "inventory unsupported")
    assert unsupported["costs"]["actions"] == 0
    report = {
        "status": "PASS",
        "python": sys.version,
        "non_editable_module": str(module),
        "kit_files_verified": len(manifest["files_sha256"]),
        "receipt": receipt,
        "inventory": unsupported,
        "scope": "Supported demo including isolated twin replay; "
        "typed refusals are preserved. Inventory is not reconstructed.",
    }
    (out / "reproduction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.kit.resolve(), args.out.resolve())
