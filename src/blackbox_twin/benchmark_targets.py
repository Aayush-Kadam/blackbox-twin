"""Evaluator-owned fixture generation. Never imported by the learning/planning modules."""

import hashlib
import json
import random
from pathlib import Path

from .contracts import Action, Target

RUNNER = """import sys,json
TABLE=json.loads(DATA)
state=0
for line in sys.stdin:
 request=json.loads(line)
 if request=={"control":"reset"}:
  state=0
  output={"control":"reset","ok":True}
 elif request.get("arguments") or request.get("operation") not in TABLE[0]:
  output={"error":"unsupported_action"}
 else:
  state,output=TABLE[state][request["operation"]]
 print(json.dumps(output),flush=True)
"""


def generate_target(root: Path, family, seed, workflow_source=None):
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("Target output must be empty")
    if family == "random":
        rng, size, alphabet = random.Random(seed), 4 + seed % 3, ["a", "b", "c"]
        table = [
            {
                a: [
                    (state + 1) % size if a == "a" else rng.randrange(size),
                    {"symbol": str(rng.randrange(3))},
                ]
                for a in alphabet
            }
            for state in range(size)
        ]
        parameters = {"states": size, "alphabet": 3, "outputs": 3, "reachable": True}
    elif family == "delayed":
        depth, alphabet = 3 + seed % 4, ["advance", "commit", "idle"]
        table = [
            {
                "advance": [min(i + 1, depth), {"ok": True}],
                "commit": [0, {"result": "accepted" if i == depth else "denied"}],
                "idle": [i, {"ok": True}],
            }
            for i in range(depth + 1)
        ]
        parameters = {"depth": depth, "states": depth + 1}
    elif family == "workflow":
        # Reuse the existing owned order fixture, not a learner-visible transition table.
        alphabet = ["create", "authorize", "capture", "refund", "cancel", "status"]
        original = (
            Path(workflow_source)
            if workflow_source
            else Path(__file__).resolve().parents[2] / "fixtures/targets/order_process.py"
        )
        (root / "oracle.py").write_bytes(original.read_bytes())
        parameters = {"variant": "order-processing-v1", "same_target_across_selection_seeds": True}
        table = None
    else:
        raise ValueError("Unknown benchmark family")
    if table is not None:
        source = RUNNER.replace("DATA", repr(json.dumps(table)))
        (root / "oracle.py").write_text(source, encoding="utf-8")
    target = Target(
        target_id=f"m4-{family}-{seed}",
        version="1",
        executable="oracle.py",
        authorization="owned-local-fixture",
        actions={s: Action(operation=s) for s in alphabet},
    )
    (root / "target.json").write_text(target.model_dump_json(indent=2), encoding="utf-8")
    (root / "generation.json").write_text(
        json.dumps(
            {
                "family": family,
                "seed": seed,
                "parameters": parameters,
                "oracle_sha256": hashlib.sha256((root / "oracle.py").read_bytes()).hexdigest(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return target, root / "oracle.py"
