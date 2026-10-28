"""Inventory installed licenses and query OSV for exact Python/npm package versions.

No credentials or local artifacts are uploaded: only public package names and versions.
Network failures are recorded as UNKNOWN, never a clean vulnerability result.
"""

import argparse
import importlib.metadata as metadata
import json
import subprocess
import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def fetch(url, destination, payload=None):
    args = [
        "curl.exe",
        "--compressed",
        "--silent",
        "--show-error",
        "--connect-timeout",
        "5",
        "--max-time",
        "35",
        "--output",
        str(destination),
        url,
    ]
    if payload:
        args.extend(
            ["--header", "Content-Type: application/json", "--data-binary", "@" + str(payload)]
        )
    result = subprocess.run(args, capture_output=True, text=True, timeout=40)
    if result.returncode:
        return {"status": "UNKNOWN", "error": result.stderr.strip(), "url": url}
    try:
        return {
            "status": "retrieved",
            "data": json.loads(destination.read_text(encoding="utf-8")),
            "url": url,
        }
    except (OSError, ValueError) as exc:
        return {"status": "UNKNOWN", "error": str(exc), "url": url}


def run(project, out):
    out.mkdir(parents=True)
    names = set()
    for lock in (
        "requirements-lock.txt",
        "requirements-workbench-lock.txt",
        "requirements-m8-lock.txt",
    ):
        if not (project / lock).exists():
            continue
        names.update(
            s.split("==")[0].lower().replace("_", "-")
            for s in (project / lock).read_text().splitlines()
            if "==" in s and not s.startswith("#")
        )
    pending = list(names)
    while pending:
        try:
            dist = metadata.distribution(pending.pop())
        except metadata.PackageNotFoundError:
            continue
        for value in dist.requires or []:
            requirement = Requirement(value)
            name = requirement.name.lower().replace("_", "-")
            if (not requirement.marker or requirement.marker.evaluate()) and name not in names:
                names.add(name)
                pending.append(name)
    inventory, queries = [], []
    for name in sorted(names):
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            inventory.append({"name": name, "status": "NOT_INSTALLED"})
            continue
        license_files = []
        for path in dist.files or []:
            if any(
                word in Path(str(path)).name.upper() for word in ("LICENSE", "COPYING", "NOTICE")
            ):
                source = Path(dist.locate_file(path))
                if source.is_file() and source.stat().st_size < 200000:
                    destination = out / "licenses" / name / Path(str(path)).name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
                    license_files.append(destination.relative_to(out).as_posix())
        inventory.append(
            {
                "name": name,
                "version": dist.version,
                "license_expression": dist.metadata.get("License-Expression"),
                "license_metadata": dist.metadata.get("License"),
                "license_files": license_files,
                "requires_python": dist.metadata.get("Requires-Python"),
                "requires_dist": dist.metadata.get_all("Requires-Dist") or [],
            }
        )
        queries.append({"package": {"name": name, "ecosystem": "PyPI"}, "version": dist.version})
    for value in tomllib.loads((project / "pyproject.toml").read_text())["build-system"][
        "requires"
    ]:
        requirement = Requirement(value)
        version = next(iter(requirement.specifier)).version
        if not any(q["package"]["name"] == requirement.name for q in queries):
            queries.append(
                {"package": {"name": requirement.name, "ecosystem": "PyPI"}, "version": version}
            )
            inventory.append({"name": requirement.name, "version": version, "scope": "build-only"})
    for path in sorted((project / "frontend/node_modules").glob("*/package.json")):
        info = json.loads(path.read_text(encoding="utf-8"))
        if info["name"] not in {"react", "react-dom", "scheduler", "esbuild", "prettier"}:
            continue
        inventory.append(
            {
                "name": info["name"],
                "version": info["version"],
                "ecosystem": "npm",
                "license_metadata": info.get("license"),
            }
        )
        queries.append(
            {"package": {"name": info["name"], "ecosystem": "npm"}, "version": info["version"]}
        )
        for source in path.parent.glob("*LICENSE*"):
            if source.is_file():
                destination = out / "licenses/npm" / info["name"] / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
    request = out / "osv-query.json"
    request.write_text(json.dumps({"queries": queries}), encoding="utf-8")
    response = fetch("https://api.osv.dev/v1/querybatch", out / "osv-response.json", request)
    records = []
    if response["status"] == "retrieved" and len(response["data"].get("results", [])) == len(
        queries
    ):
        for query, result in zip(queries, response["data"]["results"], strict=True):
            records.append({**query, "advisories": result.get("vulns", [])})
        status = "QUERY_COMPLETED"
    else:
        status = "UNKNOWN"
    report = {
        "audit_status": status,
        "inventory": inventory,
        "queries": len(queries),
        "advisory_service": response,
        "records": records,
        "scope": "OSV exact-version lookup is not proof of absence of vulnerabilities. "
        "Frontend optional platform esbuild binaries share the esbuild version; "
        "all lockfile entries remain subject to separate registry audit.",
    }
    (out / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "packages": len(inventory),
                "queries": len(queries),
                "with_advisories": [r for r in records if r["advisories"]],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.out.resolve())
