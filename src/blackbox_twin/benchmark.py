"""Sequential paired pilot: common L*, physical budgets, frozen independent evaluation."""

import hashlib
import json
import platform
import random
import sqlite3
import time
from pathlib import Path

from .benchmark_targets import generate_target
from .cli import load_target
from .contracts import BehavioralModel, QueryBudget
from .differential import json_differences
from .learning import LearningStalled, learn
from .oracle import BudgetExhausted, OracleFailure, ProcessOracle, Session
from .planner_oracles import ReplayCacheSUL, SelectionOracle
from .refinement import phase_costs, write_json
from .storage import Recorder, utc_now
from .synthesis import generate_twin


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def source_digest():
    root = Path(__file__).parent
    files = [
        "benchmark.py",
        "benchmark_targets.py",
        "planning.py",
        "planner_oracles.py",
        "learning.py",
        "oracle.py",
        "contracts.py",
        "storage.py",
        "differential.py",
        "benchmark_summary.py",
    ]
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files})


def benchmark_recorder(path, metadata):
    recorder = Recorder(path, metadata)
    # Uniform across ALL methods and evaluator; preserve process-crash committed events.
    recorder.db.execute("PRAGMA journal_mode=WAL")
    recorder.db.execute("PRAGMA synchronous=NORMAL")
    return recorder


class Checkpoints:
    def __init__(self, session, folder, ceilings):
        self.session, self.folder, self.ceilings = session, folder, ceilings
        self.current, self.model_cost, self.revisions, self.points = None, 0, 0, {}

    def capture(self, ceiling, spent):
        filename = None
        if self.current is not None:
            filename = f"model-{ceiling:05}.json"
            (self.folder / filename).write_text(
                self.current.model_dump_json(indent=2), encoding="utf-8"
            )
        point = {
            "ceiling": ceiling,
            "actual_actions": spent,
            "actual_resets": self.session.costs.resets,
            "model": filename,
            "model_generated_at_actions": self.model_cost,
            "model_states": len(self.current.transitions) if self.current else 0,
        }
        self.points[ceiling] = point
        write_json(self.folder / f"point-{ceiling:05}.json", point)

    def on_action(self):
        count = self.session.costs.actions
        if count in self.ceilings:
            self.capture(count, count)

    def on_model(self, model):
        self.current, self.model_cost = model, self.session.costs.actions
        self.revisions += 1
        if self.model_cost in self.ceilings:
            self.capture(self.model_cost, self.model_cost)


class CheckpointSession(Session):
    def step(self, symbol):
        result = super().step(symbol)
        self.tracker.on_action()
        return result


def train_cell(target, script, folder, config, method, seed):
    folder.mkdir(parents=True)
    ceilings = config["budgets"]
    budget = QueryBudget(
        max_actions=max(ceilings),
        max_resets=config["max_resets"],
        max_sequence_length=100,
        total_seconds=float(config["seconds_per_run"]),
    )
    recorder = benchmark_recorder(
        folder / "observations.sqlite",
        {
            "target": target.model_dump(),
            "method": method,
            "seed": seed,
            "budget": budget.model_dump(),
            "cache": "common-prefix-replay-v1",
        },
    )
    original = ProcessOracle(script)
    session = CheckpointSession(original, target, budget, recorder, "reset-validation")
    tracker = Checkpoints(session, folder, ceilings)
    session.tracker = tracker
    delegated = []
    status, stats, started = "failed", {}, time.perf_counter()

    def factory(alphabet, sul):
        oracle = SelectionOracle(
            alphabet,
            sul,
            method,
            seed,
            pool_size=config["pool_size"],
            max_length=config["max_length"],
        )
        delegated.append(oracle)
        return oracle

    try:
        session.verify_reset()
        session.phase = "membership"
        _, stats = learn(
            session,
            folder / "latest-model.json",
            seed=seed,
            equivalence_factory=factory,
            checkpoint_hook=tracker.on_model,
            sul_factory=ReplayCacheSUL,
            provenance={"method": method, "seed": seed},
        )
        status = "search_completed"
    except BudgetExhausted as exc:
        status = (
            "budget_exhausted" if str(exc) == "physical_action_budget" else "failed:" + str(exc)
        )
    except (OracleFailure, LearningStalled) as exc:
        status = "failed:" + type(exc).__name__ + ":" + str(exc)
    except BaseException:
        status = "interrupted"
        raise
    finally:
        session.post(status)
        original.close()
        if status in {"budget_exhausted", "search_completed"}:
            for ceiling in ceilings:
                if ceiling not in tracker.points:
                    tracker.capture(ceiling, session.costs.actions)
        replay = getattr(session, "replay_cache", None)
        learning_cache = getattr(getattr(session, "learning_oracle", None), "sul", None)
        selected = delegated[0] if delegated else None
        summary = {
            "schema_version": 1,
            "status": status,
            "method": method,
            "seed": seed,
            "costs": session.costs.model_dump(),
            "points": list(tracker.points.values()),
            "revisions": tracker.revisions,
            "statistics": stats,
            "counterexamples": selected.counterexamples if selected else [],
            "planner_seconds": selected.planning_seconds if selected else 0.0,
            "selection_compute_seconds": selected.planner.planning_seconds if selected else 0.0,
            "cache_prefix_outputs": replay.cache_actions if replay else 0,
            "cache_complete_traces": replay.cache_traces if replay else 0,
            "membership_cache_hits": getattr(learning_cache, "num_cached_queries", 0),
            "membership_logical_queries": getattr(learning_cache, "num_queries", 0),
            "wall_seconds": time.perf_counter() - started,
            "phase_costs": phase_costs(recorder),
            "unique_physical_sequences": recorder.db.execute(
                "SELECT COUNT(DISTINCT actions) FROM experiments WHERE status='completed'"
            ).fetchone()[0],
        }
        if tracker.current is not None:
            generate_twin(tracker.current, folder / "twin.py")
        recorder.artifact("benchmark_training", summary)
        recorder.close(status)
        write_json(folder / "training.json", summary)
    return summary


def reference_set(target, script, folder, config, seed):
    folder.mkdir(parents=True, exist_ok=True)
    rng = random.Random(config["evaluation_seed_offset"] + seed)
    words = []
    while len(words) < config["evaluation_count"]:
        word = [
            rng.choice(list(target.actions))
            for _ in range(
                rng.randint(config["evaluation_min_length"], config["evaluation_max_length"])
            )
        ]
        if word not in words:
            words.append(word)
    frozen = {
        "schema_version": 1,
        "created_at": utc_now(),
        "seed": seed,
        "target_id": target.target_id,
        "sequences": words,
    }
    write_json(folder / "inputs.json", frozen)
    recorder = benchmark_recorder(folder / "observations.sqlite", {"target": target.model_dump()})
    original = ProcessOracle(script)
    session = Session(
        original,
        target,
        QueryBudget(max_actions=sum(map(len, words)), max_resets=len(words), total_seconds=120.0),
        recorder,
        "held-out-reference",
    )
    try:
        traces = [[o.payload for o in session.trace(word)] for word in words]
        result = {**frozen, "outputs": traces, "costs": session.costs.model_dump()}
        write_json(folder / "references.json", result)
        recorder.close("completed")
    finally:
        original.close()
    return result


def score_points(folder, summary, reference):
    # Invoked AFTER training returns. No evaluation file/outputs enter train_cell.
    with sqlite3.connect(folder / "observations.sqlite") as db:
        training_words = {
            tuple(json.loads(row[0])) for row in db.execute("SELECT actions FROM experiments")
        }
    if training_words.intersection(map(tuple, reference["sequences"])):
        raise ValueError("Frozen held-out input overlaps training")
    points = []
    for point in sorted(summary["points"], key=lambda p: p["ceiling"]):
        model = (
            BehavioralModel.model_validate_json((folder / point["model"]).read_text())
            if point["model"]
            else None
        )
        exact = step_matches = steps = 0
        for word, truth in zip(reference["sequences"], reference["outputs"], strict=True):
            predicted = [o.payload for o in model.predict(word)] if model else None
            exact += predicted is not None and not json_differences(predicted, truth)[0]
            steps += len(word)
            if predicted:
                step_matches += sum(
                    not json_differences(a, b)[0] for a, b in zip(predicted, truth, strict=True)
                )
        points.append(
            {
                **point,
                "trace_matches": exact,
                "traces": len(reference["sequences"]),
                "trace_fidelity": exact / len(reference["sequences"]),
                "step_matches": step_matches,
                "steps": steps,
                "step_fidelity": step_matches / steps,
                "unsupported_trace_rate": 1.0 if model is None else 0.0,
            }
        )
    return points


def run_suite(manifest_path: Path, out: Path, resume=False):
    config = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        config["budgets"] != sorted(set(config["budgets"]))
        or min(config["budgets"]) < 1
        or config["evaluation_min_length"] <= config["max_length"]
    ):
        raise ValueError("Invalid checkpoint/evaluation protocol")
    identity = digest(config)
    source_identity = source_digest()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "config.json").exists():
        if (
            not resume
            or json.loads((out / "config.json").read_text())["manifest_sha256"] != identity
            or json.loads((out / "config.json").read_text()).get("source_sha256") != source_identity
        ):
            raise ValueError("Use --resume with the identical frozen manifest")
    elif any(out.iterdir()):
        raise ValueError("Suite output must be empty")
    else:
        write_json(
            out / "config.json",
            {
                "manifest_sha256": identity,
                "source_sha256": source_identity,
                "protocol": config,
                "created_at": utc_now(),
                "python": platform.python_version(),
            },
        )
    for family in config["families"]:
        for seed in config["seeds"]:
            pair = out / family / str(seed)
            target_folder = pair / "target"
            if (target_folder / "target.json").exists():
                target, script = load_target(target_folder / "target.json")
            else:
                target, script = generate_target(
                    target_folder, family, seed, manifest_path.parent / config["workflow_source"]
                )
            ref_file = pair / "evaluation/references.json"
            generation = json.loads((target_folder / "generation.json").read_text())
            if hashlib.sha256(script.read_bytes()).hexdigest() != generation["oracle_sha256"]:
                raise ValueError("Generated target fingerprint changed")
            reference = (
                json.loads(ref_file.read_text())
                if ref_file.exists()
                else reference_set(target, script, pair / "evaluation", config, seed)
            )
            for method in config["methods"]:
                cell = pair / method
                receipt = cell / "result.json"
                if receipt.exists():
                    continue
                cell.mkdir(parents=True, exist_ok=True)
                attempt = cell / f"attempt-{len(list(cell.glob('attempt-*'))):03}"
                training_config = {
                    k: config[k]
                    for k in ("budgets", "max_resets", "seconds_per_run", "pool_size", "max_length")
                }
                selection_seed = config.get("selection_seed_offset", 0) + seed
                summary = train_cell(
                    target, script, attempt, training_config, method, selection_seed
                )
                points = score_points(attempt, summary, reference)
                result = {
                    "schema_version": 1,
                    "family": family,
                    "seed": seed,
                    "method": method,
                    "attempt": attempt.name,
                    "prior_incomplete_attempts": len(list(cell.glob("attempt-*"))) - 1,
                    "target_contract_sha256": digest(target.model_dump()),
                    "oracle_sha256": generation["oracle_sha256"],
                    "evaluation_sha256": digest(reference),
                    "manifest_sha256": identity,
                    "training": summary,
                    "points": points,
                    "evaluation_cost_shared_per_pair": reference["costs"],
                }
                write_json(receipt, result)
                print(
                    json.dumps(
                        {
                            "family": family,
                            "seed": seed,
                            "method": method,
                            "status": summary["status"],
                            "actions": summary["costs"]["actions"],
                        }
                    ),
                    flush=True,
                )
    from .benchmark_summary import summarize

    return summarize(out)
