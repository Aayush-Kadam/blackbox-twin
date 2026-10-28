"""Bounded M7 demonstration using the existing M3 learning/refinement pipeline."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from .cli import load_target
from .contracts import BehavioralModel, QueryBudget
from .m3_evaluation import evaluate_pair, freeze_sequences
from .oracle import oracle_environment
from .refinement import run_loop
from .storage import utc_now


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def run_demo(project, out):
    """No caller-selected target, source, executable, seed or unbounded budget."""
    out.mkdir(parents=True)
    started = time.perf_counter()
    config = {
        "schema_version": 1,
        "fixture": "delayed-commit",
        "learner_seed": 7,
        "evaluation_seed": 20261027,
        "evaluation_count": 100,
        "training_budget": {"max_actions": 6000, "max_resets": 2000, "seconds": 90},
        "evaluation_budget": {"max_actions": 6000, "max_resets": 1000, "seconds": 90},
        "started_at": utc_now(),
        "scope": "demonstration, not a new benchmark",
    }
    write(out / "config.json", config)

    def phase(stage, **extra):
        write(out / "progress.json", {"stage": stage, **extra})

    try:
        target, script = load_target(project / "examples/delayed/target.json")
        # Reject edited manifests pointing outside the explicitly approved owned fixture.
        if (
            not script.is_relative_to(project)
            or script != (project / "fixtures/targets/delayed_process.py").resolve()
        ):
            raise ValueError("Demo executable is outside the fixture allowlist")
        frozen = out / "heldout-sequences.json"
        freeze_sequences(target, frozen, seed=20261027, count=100)
        config.update(
            fixture_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
            target_manifest_sha256=hashlib.sha256(
                (project / "examples/delayed/target.json").read_bytes()
            ).hexdigest(),
            frozen_inputs_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),
            package_source_sha256={
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob("*.py")
            },
        )
        write(out / "config.json", config)
        phase("learning, differential discovery, minimization and refinement")
        summary = run_loop(
            target,
            script,
            out / "loop",
            QueryBudget(max_actions=6000, max_resets=2000, total_seconds=90),
            seed=7,
            max_iterations=2,
            candidates=100,
        )
        if not summary["resolved_counterexamples"]:
            raise ValueError("No counterexample was resolved; inspect the preserved loop evidence")
        initial = BehavioralModel.model_validate_json(
            (out / "loop/revisions/000/model.json").read_text()
        )
        final = BehavioralModel.model_validate_json(
            (out / "loop" / summary["revisions"][-1]["model"]).read_text()
        )
        phase("separate frozen evaluation")
        evaluation = evaluate_pair(
            target,
            script,
            initial,
            final,
            frozen,
            out / "loop/observations.sqlite",
            out / "evaluation",
            QueryBudget(max_actions=6000, max_resets=1000, total_seconds=90),
        )
        phase("isolated standalone twin replay")
        isolated = out / "isolated"
        isolated.mkdir()
        twin = isolated / "twin.py"
        twin.write_bytes((out / "loop" / summary["revisions"][-1]["twin"]).read_bytes())
        actions = ["advance"] * 4 + ["commit"]
        state, expected = final.initial_state, [{"control": "reset", "ok": True}]
        for symbol in actions:
            edge = final.transitions[state][symbol]
            expected.append(edge.output.payload)
            state = edge.next_state
        requests = [{"control": "reset"}, *[target.actions[s].model_dump() for s in actions]]
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-u", str(twin.resolve())],
            input="".join(json.dumps(a) + "\n" for a in requests),
            capture_output=True,
            text=True,
            cwd=isolated,
            check=True,
            timeout=10,
            env=oracle_environment(),
        )
        actual = [json.loads(line) for line in result.stdout.splitlines()]
        if actual != expected:
            raise ValueError("Isolated standalone twin differs from the serialized model")
        receipt = {
            "status": "completed",
            "config": config,
            "original_training": summary["original_costs"],
            "original_evaluation": evaluation["original_costs"],
            "twin_training": summary["twin_costs"],
            "twin_evaluation": evaluation["twin_costs"],
            "isolated_twin_requests": len(requests),
            "isolated_outputs": actual,
            "resolved_counterexamples": summary["resolved_counterexamples"],
            "scores": evaluation["scores"],
            "equivalence_proven": False,
            "wall_seconds": time.perf_counter() - started,
        }
        write(out / "receipt.json", receipt)
        phase("completed")
        return receipt
    except Exception as exc:
        phase("failed", error=type(exc).__name__ + ": " + str(exc))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_demo(args.project.resolve(), args.out.resolve()), indent=2))
