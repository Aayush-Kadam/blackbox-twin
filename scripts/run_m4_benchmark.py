"""Run/resume the sequential M4 pilot with a frozen manifest."""

import argparse
import json
from pathlib import Path

from blackbox_twin.benchmark import run_suite

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()
print(json.dumps(run_suite(args.manifest, args.out, args.resume), indent=2))
