"""M3 commands registered in the existing bbt parser."""

import json
from contextlib import contextmanager
from pathlib import Path

from .contracts import BehavioralModel, Costs, QueryBudget
from .counterexamples import Corpus, minimize, model_id
from .differential import Comparison
from .experiments import discover, guided_sequences, random_sequences
from .m3_evaluation import evaluate_pair, freeze_sequences, read_prior_traces
from .oracle import ProcessOracle, Session
from .planning import planned_sequences
from .refinement import executable_runner, phase_costs, run_loop, write_json
from .storage import Recorder
from .synthesis import generate_twin

COMMANDS = {"diff", "counterexample", "refine", "loop", "holdout"}


def common(parser, model=False):
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    if model:
        parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--budget", type=int, default=6000, help="Physical original action cap")
    parser.add_argument("--reset-budget", type=int, default=2000)
    parser.add_argument("--seconds", type=float, default=300.0)
    parser.add_argument("--timeout", type=float, default=2.0)


def search_options(parser):
    parser.add_argument("--strategy", choices=["random", "guided", "cost-aware"], default="random")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--candidates", type=int, default=100)
    parser.add_argument("--max-length", type=int, default=12)
    parser.add_argument("--guided-depth", type=int, default=5)


def shrink_options(parser):
    parser.add_argument("--minimize-actions", type=int, default=1000)
    parser.add_argument("--minimize-attempts", type=int, default=200)


def add_commands(commands):
    diff = commands.add_parser("diff", help="Search a real oracle and an executable twin")
    common(diff, model=True)
    search_options(diff)
    counterexample = commands.add_parser(
        "counterexample", help="Minimize or replay persisted cases"
    )
    operations = counterexample.add_subparsers(dest="case_command", required=True)
    shrink = operations.add_parser(
        "minimize", help="Replay and deletion-minimize a comparison JSON"
    )
    common(shrink, model=True)
    shrink.add_argument("--comparison", type=Path, required=True)
    shrink_options(shrink)
    replay = operations.add_parser("replay", help="Replay a corpus discovery.json against a model")
    common(replay, model=True)
    replay.add_argument("--case", type=Path, required=True)
    for name in ("refine", "loop"):
        parser = commands.add_parser(
            name, help="Automatic budgeted counterexample-guided relearning"
        )
        common(parser, model=name == "refine")
        if name == "loop":
            parser.add_argument("--model", type=Path)
        parser.add_argument(
            "--training-db",
            type=Path,
            required=name == "refine",
            help="Required with an existing --model; never use evaluation evidence",
        )
        if name == "refine":
            parser.add_argument("--case", type=Path, required=True)
        search_options(parser)
        shrink_options(parser)
        parser.add_argument("--max-iterations", type=int, default=1 if name == "refine" else 3)
        parser.add_argument("--initial-walks", type=int, default=1)
        parser.add_argument("--initial-walk-length", type=int, default=1)
        parser.add_argument("--refinement-walks", type=int, default=10)
    holdout = commands.add_parser(
        "holdout", help="Freeze input sequences or evaluate a frozen pair"
    )
    operations = holdout.add_subparsers(dest="holdout_command", required=True)
    create = operations.add_parser("create", help="Freeze inputs BEFORE running refinement")
    create.add_argument("--target", type=Path, required=True)
    create.add_argument("--out", type=Path, required=True)
    create.add_argument("--seed", type=int, default=991)
    create.add_argument("--count", type=int, default=100)
    create.add_argument("--min-length", type=int, default=16)
    create.add_argument("--max-length", type=int, default=24)
    compare = operations.add_parser("compare", help="Separate paired executable-twin evaluation")
    common(compare)
    compare.add_argument("--initial", type=Path, required=True)
    compare.add_argument("--refined", type=Path, required=True)
    compare.add_argument("--sequences", type=Path, required=True)
    compare.add_argument("--training-db", type=Path, required=True)


def read_model(path):
    return BehavioralModel.model_validate_json(path.read_text(encoding="utf-8"))


def query_budget(args):
    return QueryBudget(
        max_actions=args.budget,
        max_resets=args.reset_budget,
        total_seconds=args.seconds,
        query_timeout_seconds=args.timeout,
    )


@contextmanager
def runtime(target, script, model, out, budget, phase):
    if model.actions != target.actions:
        raise ValueError("Model/target action contract differs")
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Output directory must be empty")
    recorder = Recorder(
        out / "observations.sqlite",
        {"target": target.model_dump(), "budget": budget.model_dump(), "model_id": model_id(model)},
    )
    original, oracle = None, None
    state = {"status": "failed"}
    twin_costs = Costs()
    try:
        oracle = ProcessOracle(script)
        original = Session(oracle, target, budget, recorder, phase)
        generate_twin(model, out / "twin.py")
        with executable_runner(original, out / "twin.py", twin_costs) as runner:
            yield runner, state
    finally:
        if original is not None:
            original.post(state["status"])
        if oracle is not None:
            oracle.close()
        state["original_costs"] = original.costs.model_dump() if original else Costs().model_dump()
        state["twin_costs"] = twin_costs.model_dump()
        state["phase_costs"] = phase_costs(recorder)
        recorder.artifact("command_summary", state)
        recorder.close(state["status"])
        write_json(out / "summary.json", state)


def execute(args):
    from .cli import load_target

    target, script = load_target(args.target)
    if args.command == "holdout":
        if args.holdout_command == "create":
            dataset = freeze_sequences(
                target, args.out, args.seed, args.count, args.min_length, args.max_length
            )
            print(json.dumps({"sequences": len(dataset["sequences"]), "path": str(args.out)}))
            return 0
        result = evaluate_pair(
            target,
            script,
            read_model(args.initial),
            read_model(args.refined),
            args.sequences,
            args.training_db,
            args.out,
            query_budget(args),
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "completed" else 2
    if args.command in {"refine", "loop"}:
        model = read_model(args.model) if args.model else None
        prior = read_prior_traces(args.training_db, target) if args.training_db else None
        case = Corpus.read(args.case) if args.command == "refine" else None
        summary = run_loop(
            target,
            script,
            args.out,
            query_budget(args),
            seed=args.seed,
            strategy=args.strategy,
            max_iterations=args.max_iterations,
            candidates=args.candidates,
            max_length=args.max_length,
            guided_depth=args.guided_depth,
            initial_walks=args.initial_walks,
            initial_walk_length=args.initial_walk_length,
            refinement_walks=args.refinement_walks,
            minimize_actions=args.minimize_actions,
            minimize_attempts=args.minimize_attempts,
            initial_model=model,
            supplied_counterexample=case,
            prior_traces=prior,
        )
        print(json.dumps(summary, indent=2))
        return (
            0
            if summary["status"]
            in {"no_counterexample_under_search_policy", "max_iterations_reached"}
            else 2
        )
    model = read_model(args.model)
    with runtime(target, script, model, args.out, query_budget(args), args.command) as (
        runner,
        state,
    ):
        if args.command == "diff":
            proposals = (
                planned_sequences(
                    model, {}, args.seed, args.candidates, args.max_length, args.budget
                )
                if args.strategy == "cost-aware"
                else (
                    random_sequences(
                        list(model.actions), args.seed, args.candidates, 1, args.max_length
                    )
                    if args.strategy == "random"
                    else guided_sequences(
                        model, args.guided_depth, args.candidates, args.max_length
                    )
                )
            )
            result = discover(runner, proposals)
            state["status"] = result.status if result else "no_counterexample"
            if result:
                write_json(args.out / "comparison.json", result.model_dump())
        elif args.case_command == "replay":
            record = Corpus.read(args.case)
            if record.target_id != target.target_id or record.target_version != target.version:
                raise ValueError("Counterexample target differs")
            result = runner.run(record.minimization.minimized.actions)
            state.update({"status": result.status, "counterexample_id": record.counterexample_id})
            write_json(args.out / "comparison.json", result.model_dump())
        else:
            initial = Comparison.model_validate_json(args.comparison.read_text(encoding="utf-8"))
            result = minimize(runner, initial, args.minimize_actions, args.minimize_attempts)
            write_json(args.out / "minimization.json", result.model_dump())
            state["status"] = result.status
            if result.minimized is not None:
                corpus = Corpus(args.out / "counterexamples")
                record = corpus.add(
                    target,
                    model,
                    result,
                    "replay-minimization",
                    0,
                    runner.original.costs.model_dump(),
                )
                state["counterexample_id"] = record.counterexample_id
    print(json.dumps(state, indent=2))
    if state["status"] in {"agreement", "no_counterexample", "completed"}:
        return 0
    return 3 if state["status"].endswith("disagreement") else 2
