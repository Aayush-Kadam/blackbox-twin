"""Bounded non-editable package/data-kit smoke, independent of the M6 campaign runner."""

import subprocess
import sys
from pathlib import Path


def run(root):
    out = root / "work/ci-package"
    out.mkdir(parents=True)
    (wheel,) = (root / "wheelhouse").glob("blackbox_twin-*.whl")
    subprocess.run([sys.executable, "-m", "venv", str(out / "venv")], check=True)
    python = out / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-r",
            str(root / "requirements-m8-lock.txt"),
            str(wheel),
        ],
        check=True,
        timeout=240,
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/build_m8_kit.py"),
            "--project",
            str(root),
            "--out",
            str(out / "kit"),
        ],
        check=True,
        timeout=30,
    )
    subprocess.run(
        [
            str(python),
            "-I",
            str(root / "scripts/reproduce_m8.py"),
            "--kit",
            str(out / "kit"),
            "--out",
            str(out / "reproduction"),
        ],
        check=True,
        timeout=240,
    )


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
