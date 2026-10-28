"""Complete M7 reproduction from an independently installed non-editable package."""

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import blackbox_twin
from blackbox_twin.contracts import BehavioralModel
from blackbox_twin.m7_data import read, sha
from blackbox_twin.m7_demo import run_demo
from blackbox_twin.workbench import create_app


def reproduce(project, previous, out):
    module = Path(blackbox_twin.__file__).resolve()
    assert module.is_relative_to(Path(sys.prefix).resolve())
    direct = json.loads(
        importlib.metadata.distribution("blackbox-twin").read_text("direct_url.json")
    )
    assert not direct.get("dir_info", {}).get("editable", False)
    receipt = run_demo(project, out)
    prior = read(previous / "receipt.json")
    assert receipt["scores"] == prior["scores"]
    for side in ("original_training", "original_evaluation", "twin_training", "twin_evaluation"):
        assert all(receipt[side][k] == prior[side][k] for k in ("actions", "resets"))
    for revision in ("000", "001"):
        left = BehavioralModel.model_validate(
            read(out / "loop/revisions" / revision / "model.json")
        )
        right = BehavioralModel.model_validate(
            read(previous / "loop/revisions" / revision / "model.json")
        )
        assert left.model_dump(exclude={"provenance"}) == right.model_dump(exclude={"provenance"})
    with TestClient(create_app(project, out / "unused-server-runs")) as client:
        assert client.get("/").status_code == 200
        assets = {}
        for name in ("app.js", "app.css", "index.html", "app.js.LEGAL.txt"):
            path = module.parent / "workbench_assets" / name
            assert path.is_file()
            assert sha(path) == sha(project / "src/blackbox_twin/workbench_assets" / name)
            assets[name] = sha(path)
        assert client.get("/assets/app.js").status_code == 200
        assert (
            client.get("/api/experiments/m3-replay").json()["physical_training"]["actions"] == 1855
        )
        assert len(client.get("/api/benchmarks").json()["cells"]) == 324
        assert {v["status"] for v in client.get("/api/typed").json()["examples"]} == {
            "OBSERVED",
            "INFERRED_SUPPORTED",
            "AMBIGUOUS",
            "UNSUPPORTED",
        }
    report = {
        "verification": "PASS",
        "non_editable": True,
        "installed_module": str(module),
        "installation": direct,
        "same_behavioral_tables": True,
        "same_physical_costs": True,
        "same_frozen_scores": True,
        "packaged_assets": assets,
        "receipt": receipt,
        "scope": "One supported full demo reproduced. No inventory reconstruction claim.",
    }
    (out / "reproduction.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--compare", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reproduce(args.project.resolve(), args.compare.resolve(), args.out.resolve())
