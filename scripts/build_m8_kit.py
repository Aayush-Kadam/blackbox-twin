"""Create a declared, hash-listed local review data kit; never publish it."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def build(project, out):
    out.mkdir(parents=True)
    names = ["examples/delayed/target.json", "fixtures/targets/delayed_process.py"]
    names += [
        p.relative_to(project).as_posix()
        for p in (project / "evidence/m3-demo").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    names += [
        "evidence/m6-confirmatory-v1/" + name
        for name in ("results.json", "summary.json", "protocol.json")
    ]
    typed = "evidence/m6-confirmatory-v1/B-wallet-1/seed-1-hardened-1500/training/attempt-000/"
    names += [typed + name for name in ("scored.json", "integrity.json")]
    files = {}
    for name in sorted(names):
        source, destination = project / name, out / name
        assert source.resolve().is_relative_to(project)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        files[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest = {
        "status": "LOCAL REVIEW ONLY; public publication requires separate owner approval",
        "scope": "Curated data subset: M3 replay, M6 aggregate tables and one wallet policy. "
        "Not the full M6 campaign or its full integrity closure.",
        "files_sha256": files,
    }
    (out / "kit-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(files), "bytes": sum((out / n).stat().st_size for n in files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    build(args.project.resolve(), args.out.resolve())
