"""Create frozen development/confirmation protocols, run sequentially, or resume completed cells."""

import argparse
import json
import random
from pathlib import Path

from blackbox_twin.m5 import write
from blackbox_twin.m6_run import run_campaign, source_hashes, summarize
from blackbox_twin.storage import utc_now

ROOT = Path(__file__).resolve().parents[1]


def protocol(pilot=False):
    targets = []
    target_seeds = random.Random(62719).sample(range(80000, 90000), 12)
    for family in ("easy", "medium", "delayed", "rare"):
        for variant in range(3):
            targets.append(
                {
                    "id": f"A-{family}-{variant}",
                    "track": "A",
                    "family": family,
                    "variant": variant,
                    "target_seed": target_seeds[len(targets)],
                }
            )
    parameters = [
        (1, 4, 1, True, False),
        (2, 2, 1, True, False),
        (2, 4, 2, True, False),
        (3, 1, 1, False, False),
        (3, 4, 2, True, False),
        (4, 4, 1, True, True),
    ]
    for i, (cap, limit, minimum, blocks, keep) in enumerate(parameters):
        targets.append(
            {
                "id": f"B-wallet-{i}",
                "track": "B",
                "family": "wallet",
                "variant": i,
                "target_seed": None,
                "parameters": {
                    "cap": cap,
                    "limit": limit,
                    "minimum": minimum,
                    "freeze_blocks": blocks,
                    "withdraw_keep": keep,
                },
            }
        )
    for i in range(3):
        targets.append(
            {
                "id": f"C-inventory-{i}",
                "track": "C",
                "family": "inventory",
                "variant": i,
                "target_seed": None,
                "parameters": {"cap": i + 2, "limit": i + 1},
            }
        )
    if pilot:
        targets = [targets[0], targets[12], targets[18]]
        targets[0] = {**targets[0], "id": "dev-A", "target_seed": 71}
        targets[1] = {
            **targets[1],
            "id": "dev-B",
            "parameters": {
                "cap": 2,
                "limit": 3,
                "minimum": 1,
                "freeze_blocks": True,
                "withdraw_keep": False,
            },
        }
        targets[2] = {**targets[2], "id": "dev-C", "parameters": {"cap": 2, "limit": 2}}
    resources = [
        "fixtures/targets/typed_wallet_process.py",
        "examples/typed_wallet/contract.json",
        "evidence/m4-1/target-rare-access/oracle.py",
    ]
    from blackbox_twin.m6_run import sha

    return {
        "schema_version": 1,
        "protocol_id": "M6-development-v1" if pilot else "M6-confirmatory-v1",
        "frozen_at": utc_now(),
        "label": "DEVELOPMENT ONLY" if pilot else "CONFIRMATORY",
        "source_sha256": source_hashes(),
        "resources_sha256": {n: sha(ROOT / n) for n in resources},
        "targets": targets,
        "learner_seeds": random.Random(13711).sample(range(15000, 19000), 3),
        "training_seeds": random.Random(22817).sample(range(27000, 31000), 3),
        "evaluation_seeds": random.Random(71983).sample(range(95000, 105000), len(targets)),
        "finite_seed_count": 1 if pilot else 3,
        "typed_seed_count": 1 if pilot else 2,
        "reserved_values": [-7, -5, -3, 3, 6, 7],
        "budgets": {
            "A": [250] if pilot else [250, 1000],
            "B": [1500] if pilot else [1500, 3000],
            "C": [500] if pilot else [500, 1500],
        },
        "methods": {
            "A": ["aalpy-state-prefix", "aalpy-random-w", "random"],
            "B": ["fixed-grid", "adaptive", "hardened"],
            "C": ["fixed-grid", "adaptive", "hardened"],
        },
        "criterion": {"trace_fidelity": 0.95, "output_coverage": 0.95},
        "seed_scope": "target RNG for A; typed targets are fixed configurations, not random draws",
        "statistical_scope": (
            "target-level seed means, descriptive medians/ranges; no population CI"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["freeze", "run", "summary"])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.operation == "freeze":
        if args.manifest is None or args.manifest.exists():
            raise ValueError("Choose a new manifest path")
        write(args.manifest, protocol(args.pilot))
        result = {"frozen_manifest": str(args.manifest)}
    elif args.operation == "run":
        result = run_campaign(ROOT, args.manifest, args.out, args.resume)
    else:
        result = summarize(json.loads((args.out / "results.json").read_text()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
