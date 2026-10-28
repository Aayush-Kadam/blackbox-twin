"""Save advisory details and a scoped dependency ledger from preserved OSV evidence."""

import argparse
import csv
import importlib.metadata as metadata
import json
import tomllib
from pathlib import Path

from m8_dependencies import fetch
from packaging.requirements import Requirement


def run(project, out):
    out.mkdir(parents=True)
    final = json.loads((project / "evidence/m8-dependencies-patched-build/audit.json").read_text())
    assert final["audit_status"] == "QUERY_COMPLETED"
    assert not any(record["advisories"] for record in final["records"])
    pyproject = tomllib.loads((project / "pyproject.toml").read_text())
    direct = {
        Requirement(v).name.lower().replace("_", "-")
        for v in pyproject["project"]["dependencies"]
        + sum(pyproject["project"]["optional-dependencies"].values(), [])
    }
    frontend = json.loads((project / "frontend/package.json").read_text())
    direct.update(frontend["dependencies"])
    direct.update(frontend["devDependencies"])
    runtime = {
        Requirement(v).name.lower().replace("_", "-")
        for v in pyproject["project"]["dependencies"]
        + pyproject["project"]["optional-dependencies"]["workbench"]
    }
    pending = list(runtime)
    while pending:
        for value in metadata.distribution(pending.pop()).requires or []:
            requirement = Requirement(value)
            name = requirement.name.lower().replace("_", "-")
            if (not requirement.marker or requirement.marker.evaluate()) and name not in runtime:
                runtime.add(name)
                pending.append(name)
    with (out / "dependency-ledger.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["name", "version", "relationship", "scope", "license", "advisory_status"],
        )
        writer.writeheader()
        for item in final["inventory"]:
            name = item["name"]
            writer.writerow(
                {
                    "name": name,
                    "version": item.get("version"),
                    "relationship": "direct"
                    if name in direct or name == "setuptools"
                    else "transitive",
                    "scope": "frontend dev"
                    if name in frontend["devDependencies"]
                    else "frontend runtime"
                    if item.get("ecosystem") == "npm"
                    else "build"
                    if name == "setuptools"
                    else "python runtime"
                    if name in runtime
                    else "python dev/test",
                    "license": item.get("license_expression")
                    or item.get("license_metadata")
                    or "see copied license text",
                    "advisory_status": "No listed advisories in completed exact-version OSV lookup",
                }
            )
    identifiers = set()
    for folder in ("m8-dependencies-baseline", "m8-dependencies-closure"):
        audit = json.loads((project / "evidence" / folder / "audit.json").read_text())
        identifiers.update(
            v["id"]
            for record in audit["records"]
            for v in record["advisories"]
            if v["id"].startswith("GHSA")
        )
    details = {}
    for identifier in sorted(identifiers):
        details[identifier] = fetch(
            "https://api.osv.dev/v1/vulns/" + identifier, out / (identifier + ".json")
        )
    (out / "advisory-details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    print(json.dumps({key: value["status"] for key, value in details.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.out.resolve())
