"""Local Git/worktree inventory and conservative hygiene scan; never prints matched values."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

EXCLUDED = {
    ".git",
    "node_modules",
    ".pnpm-store",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".venv",
    "work",
    "runs",
}
PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token_prefix": re.compile(
        rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
        rb"sk-(?:proj-)?[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16})"
    ),
    "literal_credential_assignment": re.compile(
        rb"""(?i)(?:api[_-]?key|access[_-]?token|password|secret)\s*[=:]\s*"""
        rb"""["']([^"'\r\n]{8,256})["']"""
    ),
    "personal_windows_path": re.compile(rb"(?i)[A-Z]:(?:\\+|/)Users(?:\\+|/)[^\\/\s\"']+"),
    "email": re.compile(rb"@[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,24}"),
    "environment_repr": re.compile(rb"(?:self = environ\(|environ\(\{)"),
}


def run(project, out):
    out.mkdir(parents=True)
    tracked = set(
        subprocess.check_output(["git", "-C", str(project), "ls-files", "-z"])
        .decode()
        .strip("\0")
        .split("\0")
    )
    rows, findings, totals = [], [], Counter()
    pending = [project]
    while pending:
        path = pending.pop()
        if path.is_symlink():
            continue
        if path.is_dir():
            if path.name not in EXCLUDED and not path.name.endswith(".egg-info") and path != out:
                pending.extend(path.iterdir())
            continue
        name = path.relative_to(project).as_posix()
        size = path.stat().st_size
        group = "evidence" if name.startswith("evidence/") else "source-docs-tools"
        totals[group + "_bytes"] += size
        totals[group + "_files"] += 1
        digest = hashlib.sha256()
        rules = Counter()
        # Bounded chunks avoid loading benchmark databases into memory.
        with path.open("rb") as stream:
            tail = b""
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                for rule, pattern in PATTERNS.items():
                    if rule == "email" and b"@" not in tail + chunk:
                        continue
                    rules[rule] += len(pattern.findall(tail + chunk))
                tail = chunk[-256:]
        flags = {key: value for key, value in rules.items() if value}
        for rule, count in flags.items():
            findings.append(
                {
                    "path": name,
                    "rule": rule,
                    "matches_upper_bound": count,
                    "git_tracked": name in tracked,
                    "note": "Values withheld; needs contextual review, not proof of secret.",
                }
            )
        rows.append(
            {
                "path": name,
                "bytes": size,
                "sha256": digest.hexdigest(),
                "git_tracked": name in tracked,
                "group": group,
                "proposed": "REVIEW_OR_DERIVE"
                if flags or group == "evidence"
                else "SOURCE_CANDIDATE",
                "flags": ";".join(flags),
            }
        )
    with (out / "worktree-inventory.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["path"]))
    summary = {
        "totals": dict(totals),
        "tracked_files": len(tracked),
        "findings_by_rule": dict(Counter(f["rule"] for f in findings)),
        "scope": "Excluded runtime/cache/build trees listed explicitly. All original evidence "
        "is preserved; no staging or removals. Regex scan cannot establish absence "
        "of secrets. Matches are withheld, not automatically secrets.",
    }
    (out / "hygiene-findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    (out / "distribution-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.out.resolve())
