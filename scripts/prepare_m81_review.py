"""Build a local allowlisted source review copy and unchanged research evidence archive."""

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

from build_m8_kit import build

SKIP = {"node_modules", ".pnpm-store", "__pycache__", ".pytest_cache", ".ruff_cache"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(project, out):
    out.mkdir(parents=True)
    source = out / "source"
    source.mkdir()
    names = ["README.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml", ".gitignore"]
    names += [p.name for p in project.glob("requirements*-lock.txt")]
    for directory in (
        ".github",
        "docs",
        "src",
        "tests",
        "scripts",
        "fixtures",
        "examples",
        "benchmarks",
        "third_party",
        "frontend",
    ):
        for path in (project / directory).rglob("*"):
            relative = path.relative_to(project)
            if (
                path.is_file()
                and not any(part in SKIP or part.endswith(".egg-info") for part in relative.parts)
                and path.name != ".test-build.cjs"
                and path.suffix != ".pyc"
            ):
                assert not path.is_symlink()
                names.append(relative.as_posix())
    redactions = []
    for name in sorted(set(names)):
        original, destination = project / name, source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = original.read_bytes()
        if name == "docs/VERIFICATION.md":
            revised = re.sub(rb"(?i)[A-Z]:[\\/]Users[\\/][^\s\"'`]+", b"<LOCAL_REVIEW_PATH>", data)
            if revised != data:
                redactions.append(
                    {
                        "path": name,
                        "original_sha256": digest(original),
                        "reason": "Personal absolute paths redacted in derived copy only.",
                    }
                )
            data = revised
        destination.write_bytes(data)
    build(project, out / "kit")
    for path in (out / "kit").rglob("*"):
        if path.is_file():
            destination = source / path.relative_to(out / "kit")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    rare = "evidence/m4-1/target-rare-access/oracle.py"
    (source / rare).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project / rare, source / rare)
    files = {
        p.relative_to(source).as_posix(): {"bytes": p.stat().st_size, "sha256": digest(p)}
        for p in source.rglob("*")
        if p.is_file()
    }
    assert not (source / "LICENSE").exists()
    archive = out / "research-evidence-REVIEW-ONLY.zip"
    archived = {}
    campaigns = ["m3-demo", "m4-confirmatory", "m5-primary", "m5-1-fresh", "m6-confirmatory-v1"]
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for campaign in campaigns:
            for path in sorted((project / "evidence" / campaign).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    name = path.relative_to(project).as_posix()
                    bundle.write(path, name)
                    archived[name] = {"sha256": digest(path), "bytes": path.stat().st_size}
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
    report = {
        "status": "LOCAL REVIEW ONLY — NOT APPROVED FOR PUBLICATION",
        "source_files": files,
        "source_bytes": sum(v["bytes"] for v in files.values()),
        "derived_document_redactions": redactions,
        "research_archive": archive.name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest(archive),
        "archived_files": archived,
        "scope": "Source candidate plus curated UI data; separate unchanged M3/M4/M5/M5.1/M6 "
        "campaign evidence. Operational logs, profiles, caches, environments and "
        "downloaded dependencies excluded. Ownership/license and CI gates remain.",
    }
    (out / "release-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"source_files", "archived_files"}},
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.out.resolve())
