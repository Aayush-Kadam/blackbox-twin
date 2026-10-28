"""Reproduce discovery, deletion shrinking, AALpy refinement and paired evaluation."""

import argparse
import json
from pathlib import Path

from blackbox_twin.cli import load_target
from blackbox_twin.contracts import BehavioralModel, QueryBudget
from blackbox_twin.m3_evaluation import evaluate_pair, freeze_sequences
from blackbox_twin.refinement import run_loop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples/delayed/target.json",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--evaluation-seed", type=int, default=20261027)
    args = parser.parse_args()
    target, script = load_target(args.target)
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise ValueError("Demo output directory must be empty")
    # Frozen before initial learning; run_loop never receives or loads this file.
    frozen = args.out / "heldout-sequences.json"
    freeze_sequences(target, frozen, seed=args.evaluation_seed, count=args.count)
    budget = QueryBudget(max_actions=6000, max_resets=2000, total_seconds=300.0)
    summary = run_loop(
        target, script, args.out / "loop", budget, seed=args.seed, max_iterations=2, candidates=100
    )
    if not summary["resolved_counterexamples"]:
        print(json.dumps(summary, indent=2))
        return 2
    initial = BehavioralModel.model_validate_json(
        (args.out / "loop/revisions/000/model.json").read_text()
    )
    final = BehavioralModel.model_validate_json(
        (args.out / "loop" / summary["revisions"][-1]["model"]).read_text()
    )
    evaluation = evaluate_pair(
        target,
        script,
        initial,
        final,
        frozen,
        args.out / "loop/observations.sqlite",
        args.out / "evaluation",
        QueryBudget(max_actions=6000, max_resets=1000, total_seconds=300.0),
    )
    print(json.dumps({"loop": summary, "held_out": evaluation}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
