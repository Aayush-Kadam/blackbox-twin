"""Collect exact-version upstream license texts from hash-verified public PyPI sdists."""

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path
from urllib.parse import urlsplit

from m8_dependencies import fetch


def run(out):
    out.mkdir(parents=True)
    records = []
    for name, version in (("aalpy", "2.0.0"), ("pydot", "4.0.1"), ("setuptools", "84.1.0")):
        metadata = fetch(
            f"https://pypi.org/pypi/{name}/{version}/json", out / f"{name}-metadata.json"
        )
        record = {"name": name, "version": version, "metadata_status": metadata["status"]}
        if metadata["status"] != "retrieved":
            records.append(record)
            continue
        source = next(v for v in metadata["data"]["urls"] if v["packagetype"] == "sdist")
        assert urlsplit(source["url"]).hostname == "files.pythonhosted.org"
        archive = out / source["filename"]
        result = subprocess.run(
            [
                "curl.exe",
                "--silent",
                "--show-error",
                "--fail",
                "--connect-timeout",
                "5",
                "--max-time",
                "60",
                "--output",
                str(archive),
                source["url"],
            ],
            capture_output=True,
            text=True,
            timeout=65,
        )
        record.update(
            url=source["url"],
            download_returncode=result.returncode,
            expected_sha256=source["digests"]["sha256"],
        )
        if result.returncode:
            record["status"] = "DOWNLOAD_FAILED"
            records.append(record)
            continue
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == source["digests"]["sha256"]
        texts = []
        with tarfile.open(archive) as bundle:
            for member in bundle:
                if (
                    member.isfile()
                    and member.size < 200000
                    and (
                        Path(member.name)
                        .name.upper()
                        .startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE"))
                        or any(part.upper() == "LICENSES" for part in Path(member.name).parts)
                    )
                ):
                    relative = Path(*Path(member.name).parts[1:])
                    assert ".." not in relative.parts and not relative.is_absolute()
                    destination = out / "texts" / name / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    data = bundle.extractfile(member).read()
                    destination.write_bytes(data)
                    texts.append(
                        {
                            "source_member": member.name,
                            "file": destination.relative_to(out).as_posix(),
                            "sha256": hashlib.sha256(data).hexdigest(),
                        }
                    )
        record.update(status="VERIFIED_SDIST", texts=texts)
        records.append(record)
    (out / "provenance.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(
        json.dumps(
            [{k: v for k, v in r.items() if k not in {"url", "texts"}} for r in records], indent=2
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.out.resolve())
