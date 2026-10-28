"""Only implemented commands are advertised. All execution is local."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

from .contracts import BehavioralModel, QueryBudget, Target
from .defaults import DEFAULT_STRATEGY, STRATEGIES, learning_options
from .evaluation import sampled_evaluate, training_words
from .learning import learn
from .m3_cli import COMMANDS, add_commands, execute
from .oracle import BudgetExhausted, ProcessOracle, Session
from .storage import Recorder, export_database
from .synthesis import generate_twin


def load_target(path):
    path = Path(path).resolve(strict=True)
    target = Target.model_validate_json(path.read_text(encoding="utf-8"))
    script = (path.parent / target.executable).resolve(strict=True)
    return target, script


def dump(path, content):
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")


def metadata(target, budget, seed, script):
    return {
        "schema_version": 1,
        "target": target.model_dump(),
        "budget": budget.model_dump(),
        "seed": seed,
        "python": platform.python_version(),
        "platform": platform.system(),
        "dependencies": {p: importlib.metadata.version(p) for p in ("aalpy", "pydantic")},
        # Fingerprint taken by the launcher, never used as a learning feature.
        "target_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "source_version": "0.1.0.dev0",
    }


def open_session(script, target, budget, recorder, phase):
    try:
        oracle = ProcessOracle(script)
    except BaseException:
        recorder.close("initialization_failed")
        raise
    return oracle, Session(oracle, target, budget, recorder, phase)


def run_learning(args):
    target, script = load_target(args.target)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Never overwrite a previous run or stale model checkpoint.
    if any(out.iterdir()):
        raise ValueError("Run directory must be empty; choose a new --out")
    budget = QueryBudget(max_actions=args.budget, max_resets=args.reset_budget)
    config = metadata(target, budget, args.seed, script)
    dump(out / "config.json", config)
    recorder = Recorder(out / "observations.sqlite", config)
    oracle, session = open_session(script, target, budget, recorder, "reset-check")
    status, stats, exit_code = "failed", {}, 1
    try:
        session.verify_reset()
        session.phase = "training"
        model, stats = learn(
            session,
            out / "model.json",
            seed=args.seed,
            walks=args.walks,
            walk_length=args.walk_length,
            **learning_options(args.strategy, args.seed, args.walks, args.walk_length),
        )
        generate_twin(model, out / "twin.py")
        status, exit_code = "completed_sampled_search", 0
    except BudgetExhausted as exc:
        status, exit_code = f"budget_exhausted:{exc}", 2
        session.post("budget_exhausted")
    except BaseException:
        session.post("failed")
        raise
    finally:
        cleanup_error = None
        try:
            oracle.close()
        except Exception as exc:
            cleanup_error = f"{type(exc).__name__}: {exc}"
            status, exit_code = "cleanup_failed", 1
        summary = {
            "status": status,
            "physical_costs": session.costs.model_dump(),
            "aalpy_statistics": stats,
            "equivalence_proven": False,
            "checkpoint_exists": (out / "model.json").exists(),
            "cleanup_error": cleanup_error,
            "unique_outputs": recorder.db.execute(
                "SELECT COUNT(DISTINCT response) FROM events WHERE kind='action' AND status='ok'"
            ).fetchone()[0],
        }
        recorder.artifact("summary", summary)
        recorder.close(status)
        dump(out / "summary.json", summary)
        print(json.dumps(summary, indent=2))
    return exit_code


def run_evaluation(args):
    target, script = load_target(args.target)
    model_path = Path(args.model).resolve(strict=True)
    model = BehavioralModel.model_validate_json(model_path.read_text())
    if model.actions != target.actions:
        raise ValueError("Target and model action contracts differ")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Evaluation directory must be empty")
    budget = QueryBudget(
        max_actions=args.count * args.max_length,
        max_resets=args.count,
        max_sequence_length=args.max_length,
    )
    config = metadata(target, budget, args.seed, script)
    config["model_sha256"] = hashlib.sha256(model_path.read_bytes()).hexdigest()
    dump(out / "config.json", config)
    recorder = Recorder(out / "observations.sqlite", config)
    oracle, session = open_session(script, target, budget, recorder, "held-out")
    status = "failed"
    try:
        result = sampled_evaluate(
            session,
            model,
            args.count,
            args.seed,
            args.min_length,
            args.max_length,
            training_words(Path(args.training_db)),
        )
        dump(out / "evaluation.json", result)
        recorder.artifact("evaluation", result)
        status = "completed"
        print(json.dumps(result, indent=2))
        return 0 if not result["mismatches"] else 3
    finally:
        session.post(status)
        recorder.close(status)
        oracle.close()


def main():
    parser = argparse.ArgumentParser(prog="bbt", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Validate a local target interaction contract")
    inspect.add_argument("target")
    learning = commands.add_parser("learn", help="AALpy L*; native StatePrefix recommended")
    learning.add_argument("--strategy", choices=STRATEGIES, default=DEFAULT_STRATEGY)
    learning.add_argument("--target", required=True)
    learning.add_argument("--out", required=True)
    learning.add_argument("--budget", type=int, default=10000)
    learning.add_argument("--reset-budget", type=int, default=3000)
    learning.add_argument("--seed", type=int, default=7)
    learning.add_argument("--walks", type=int, default=25)
    learning.add_argument("--walk-length", type=int, default=12)
    evaluation = commands.add_parser("evaluate", help="Evaluate a frozen model in a separate run")
    evaluation.add_argument("--target", required=True)
    evaluation.add_argument("--model", required=True)
    evaluation.add_argument("--training-db", required=True)
    evaluation.add_argument("--out", required=True)
    evaluation.add_argument("--seed", type=int, default=2027)
    evaluation.add_argument("--count", type=int, default=100)
    evaluation.add_argument("--min-length", type=int, default=9)
    evaluation.add_argument("--max-length", type=int, default=20)
    replay = commands.add_parser("replay", help="Run symbolic actions against a fresh target")
    replay.add_argument("--target", required=True)
    replay.add_argument("actions", nargs="+")
    replay.add_argument("--out", required=True)
    export = commands.add_parser("export", help="Export recorded evidence to JSONL")
    export.add_argument("database", type=Path)
    export.add_argument("destination", type=Path)
    add_commands(commands)
    typed = commands.add_parser("typed", help="Bounded M5 typed-wallet reconstruction")
    typed.add_argument("--out", type=Path, required=True)
    typed.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    typed.add_argument("--development", action="store_true")
    hardened = commands.add_parser("typed-harden", help="M5.1 evidence-aware typed twins")
    hardened.add_argument("--out", type=Path, required=True)
    hardened.add_argument("--protocol", type=Path, required=True)
    hardened.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    benchmark = commands.add_parser(
        "benchmark", help="Generate, run, resume and audit paired M4 pilots"
    )
    operations = benchmark.add_subparsers(dest="benchmark_command", required=True)
    generate = operations.add_parser("generate", help="Generate an owned finite target")
    generate.add_argument("--family", choices=["random", "delayed", "workflow"], required=True)
    generate.add_argument("--seed", type=int, required=True)
    generate.add_argument("--out", type=Path, required=True)
    generate.add_argument("--workflow-source", type=Path)
    run = operations.add_parser("run", help="Sequential paired pilot; completed cells can resume")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    for command in ("summary", "audit"):
        child = operations.add_parser(command)
        child.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "typed-harden":
            from .m51 import run_fresh

            print(json.dumps(run_fresh(args.project, args.out, args.protocol), indent=2))
            return 0
        if args.command == "typed":
            from .m5 import run_demo

            print(json.dumps(run_demo(args.project, args.out, args.development), indent=2))
            return 0
        if args.command == "benchmark":
            if args.benchmark_command == "run":
                from .benchmark import run_suite

                result = run_suite(args.manifest, args.out, args.resume)
            elif args.benchmark_command == "generate":
                from .benchmark_targets import generate_target

                if args.family == "workflow" and args.workflow_source is None:
                    raise ValueError("Workflow generation requires --workflow-source")
                target, _ = generate_target(args.out, args.family, args.seed, args.workflow_source)
                result = target.model_dump()
            elif args.benchmark_command == "summary":
                from .benchmark_summary import summarize

                result = summarize(args.out)
            else:
                from .benchmark_audit import audit_suite

                result = audit_suite(args.out)
            print(json.dumps(result, indent=2))
            return 0
        if args.command in COMMANDS:
            return execute(args)
        if args.command == "inspect":
            target, script = load_target(args.target)
            print(
                json.dumps(
                    {"contract": target.model_dump(), "executable_exists": script.is_file()},
                    indent=2,
                )
            )
            return 0
        if args.command == "learn":
            if args.walks < 1 or args.walk_length < 1:
                raise ValueError("Walk counts and lengths must be positive")
            return run_learning(args)
        if args.command == "evaluate":
            if not 1 <= args.min_length <= args.max_length or args.count < 1:
                raise ValueError("Invalid evaluation sequence count or lengths")
            return run_evaluation(args)
        if args.command == "export":
            export_database(args.database, args.destination)
            return 0
        if args.command == "replay":
            target, script = load_target(args.target)
            if any(s not in target.actions for s in args.actions):
                raise ValueError("Unknown action symbol")
            destination = Path(args.out)
            if destination.exists():
                raise ValueError("Replay evidence path already exists")
            recorder = Recorder(destination, {"target": target.model_dump()})
            oracle = ProcessOracle(script)
            session = Session(oracle, target, QueryBudget(), recorder, "replay")
            status = "failed"
            try:
                print(json.dumps([o.payload for o in session.trace(args.actions)], indent=2))
                status = "completed"
            finally:
                recorder.close(status)
                oracle.close()
            return 0
    except Exception as exc:
        print(f"bbt: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
