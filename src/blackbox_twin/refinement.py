"""Budgeted counterexample-guided relearning; never patch learned transitions."""

import hashlib
import json
import time
from contextlib import contextmanager
from pathlib import Path

from .contracts import Costs
from .counterexamples import Corpus, minimize, model_id, require_finite_actions
from .differential import DifferentialRunner, json_differences
from .experiments import discover, guided_sequences, random_sequences
from .learning import LearningStalled, learn
from .oracle import BudgetExhausted, OracleFailure, ProcessOracle, Session
from .planning import planned_sequences
from .storage import Recorder, utc_now
from .synthesis import generate_twin


class LoopStop(RuntimeError):
    pass


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def phase_costs(recorder):
    rows = recorder.db.execute(
        "SELECT x.phase,e.kind,COUNT(*),SUM(e.elapsed) FROM events e "
        "JOIN experiments x ON x.id=e.experiment_id WHERE x.run_id=? "
        "GROUP BY x.phase,e.kind",
        (recorder.run_id,),
    )
    result = {}
    for phase, kind, count, elapsed in rows:
        cost = result.setdefault(phase, {"actions": 0, "resets": 0, "oracle_seconds": 0.0})
        cost["actions" if kind == "action" else "resets"] += count
        cost["oracle_seconds"] += elapsed
    return result


def observations_from_database(recorder):
    corpus = {}
    rows = recorder.db.execute(
        "SELECT id,actions FROM experiments WHERE run_id=? AND status='completed' "
        "AND phase NOT LIKE 'twin:%' ORDER BY started,id",
        (recorder.run_id,),
    ).fetchall()
    for exp, actions in rows:
        word = tuple(json.loads(actions))
        outputs = [
            json.loads(row[0])["payload"]
            for row in recorder.db.execute(
                "SELECT response FROM events WHERE experiment_id=? AND kind='action' "
                "AND status='ok' ORDER BY id",
                (exp,),
            )
        ]
        if not word or len(word) != len(outputs):
            continue
        if word in corpus and corpus[word] != outputs:
            raise LoopStop("inconsistent_observations")
        corpus[word] = outputs
    return [(word, outputs) for word, outputs in corpus.items()]


def encode_samples(traces):
    return [
        (tuple(word), [json.dumps(p, sort_keys=True, separators=(",", ":")) for p in outputs])
        for word, outputs in traces
    ]


@contextmanager
def executable_runner(original, twin_path, twin_costs):
    oracle = ProcessOracle(twin_path)
    session = Session(
        oracle, original.target, original.budget, original.recorder, "twin:" + original.phase
    )
    session.costs, session.start = twin_costs, original.start
    try:
        yield DifferentialRunner(original, session)
    finally:
        session.post("interrupted")
        oracle.close()


def revision_manifest(folder, model, index, parent, stats, counterexample_ids):
    generate_twin(model, folder / "twin.py")
    result = {
        "schema_version": 1,
        "revision": index,
        "model_id": model_id(model),
        "parent_model_id": parent,
        "states": len(model.transitions),
        "model": f"revisions/{index:03}/model.json",
        "twin": f"revisions/{index:03}/twin.py",
        "learning_statistics": stats,
        "counterexamples": counterexample_ids,
        "created_at": utc_now(),
        "model_file_sha256": hashlib.sha256((folder / "model.json").read_bytes()).hexdigest(),
        "twin_file_sha256": hashlib.sha256((folder / "twin.py").read_bytes()).hexdigest(),
    }
    write_json(folder / "revision.json", result)
    return result


def replay_regressions(runner, traces, old_model):
    report = {
        "checked": 0,
        "passed": 0,
        "previously_passing": 0,
        "previously_passing_preserved": 0,
        "new_regressions": 0,
        "failures": [],
    }
    for word, expected in traces:
        previous_pass = not json_differences(
            [o.payload for o in old_model.predict(word)], expected
        )[0]
        report["previously_passing"] += previous_pass
        comparison = runner.run(word)
        report["checked"] += 1
        if comparison.status not in {
            "agreement",
            "output_disagreement",
            "error_code_disagreement",
            "structural_disagreement",
            "sequence_length_disagreement",
        }:
            raise LoopStop(comparison.status)
        if json_differences([o.payload for o in comparison.original], expected)[0]:
            raise LoopStop("unstable_target_on_regression")
        passed = comparison.status == "agreement"
        report["passed"] += passed
        report["previously_passing_preserved"] += bool(previous_pass and passed)
        report["new_regressions"] += bool(previous_pass and not passed)
        if not passed:
            report["failures"].append(comparison.model_dump())
    return report


def run_loop(
    target,
    script,
    out: Path,
    budget,
    *,
    seed=7,
    strategy="random",
    max_iterations=3,
    candidates=100,
    max_length=12,
    guided_depth=5,
    initial_walks=1,
    initial_walk_length=1,
    refinement_walks=10,
    minimize_actions=1000,
    minimize_attempts=200,
    initial_model=None,
    supplied_counterexample=None,
    prior_traces=None,
):
    require_finite_actions(target)
    if initial_model is not None and prior_traces is None:
        raise ValueError("Loading a model for refinement requires its prior observation corpus")
    if (
        max_iterations < 0
        or candidates < 1
        or max_length < 1
        or guided_depth < 1
        or initial_walks < 1
        or initial_walk_length < 1
        or refinement_walks < 1
        or minimize_actions < 0
        or minimize_attempts < 0
    ):
        raise ValueError("Invalid loop limits")
    if strategy not in {"random", "guided", "cost-aware"}:
        raise ValueError("Unknown differential strategy")
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Loop output directory must be empty")
    config = {
        "schema_version": 1,
        "target": target.model_dump(),
        "budget": budget.model_dump(),
        "seed": seed,
        "strategy": strategy,
        "max_iterations": max_iterations,
        "candidates": candidates,
        "max_length": max_length,
        "guided_depth": guided_depth,
        "initial_walks": initial_walks,
        "initial_walk_length": initial_walk_length,
        "refinement_walks": refinement_walks,
        "minimize_actions": minimize_actions,
        "minimize_attempts": minimize_attempts,
        "loaded_initial_model": initial_model is not None,
    }
    write_json(out / "config.json", config)
    if prior_traces is not None:
        write_json(
            out / "imported-observations.json",
            [{"actions": list(word), "outputs": outputs} for word, outputs in prior_traces],
        )
    recorder = Recorder(out / "observations.sqlite", config)
    corpus = Corpus(out / "counterexamples")
    original, oracle, model = None, None, None
    twin_costs = Costs()
    summary = {
        "schema_version": 1,
        "status": "failed",
        "revisions": [],
        "iterations": [],
        "resolved_counterexamples": 0,
        "equivalence_proven": False,
    }
    started = time.monotonic()
    records = []
    completed_records = set()
    try:
        oracle = ProcessOracle(script)
        original = Session(oracle, target, budget, recorder, "initial-learning")
        folder = out / "revisions/000"
        folder.mkdir(parents=True)
        if initial_model is None:
            original.verify_reset()
            model, stats = learn(
                original,
                folder / "model.json",
                seed=seed,
                walks=initial_walks,
                walk_length=initial_walk_length,
                provenance={"run_id": recorder.run_id},
                preserve_checkpoints=True,
            )
        else:
            if initial_model.actions != target.actions:
                raise ValueError("Initial model action contract differs from target")
            model, stats = initial_model, {"loaded_existing_model": True}
            (folder / "model.json").write_text(model.model_dump_json(indent=2), encoding="utf-8")
            original.verify_reset()
        summary["revisions"].append(revision_manifest(folder, model, 0, None, stats, []))
        for iteration in range(max_iterations):
            original.check("reset")
            original.phase = f"differential-search/{iteration}"
            iteration_start = original.costs.model_copy()
            iteration_report = {"iteration": iteration, "status": "searching"}
            summary["iterations"].append(iteration_report)
            with executable_runner(original, folder / "twin.py", twin_costs) as runner:
                if supplied_counterexample is not None and iteration == 0:
                    if (
                        supplied_counterexample.target_id != target.target_id
                        or supplied_counterexample.target_version != target.version
                        or supplied_counterexample.model_id != model_id(model)
                    ):
                        raise ValueError("Counterexample target/model identity does not match")
                    found = runner.run(supplied_counterexample.minimization.minimized.actions)
                else:
                    proposals = (
                        planned_sequences(
                            model,
                            dict(observations_from_database(recorder)),
                            seed + iteration,
                            candidates,
                            max_length,
                            budget.max_actions - original.costs.actions,
                        )
                        if strategy == "cost-aware"
                        else (
                            random_sequences(
                                list(model.actions), seed + iteration, candidates, 1, max_length
                            )
                            if strategy == "random"
                            else guided_sequences(model, guided_depth, candidates, max_length)
                        )
                    )
                    found = discover(runner, proposals)
                if found is None:
                    iteration_report["status"] = "no_counterexample"
                    summary["status"] = "no_counterexample_under_search_policy"
                    break
                if not found.is_mismatch:
                    raise LoopStop(found.status)
                original.phase = f"counterexample-minimization/{iteration}"
                reduced = minimize(
                    runner, found, max_actions=minimize_actions, max_attempts=minimize_attempts
                )
                recorder.artifact("minimization", reduced.model_dump())
                if reduced.minimized is None or reduced.status not in {
                    "completed",
                    "budget_exhausted",
                }:
                    raise LoopStop(reduced.status)
                record = corpus.add(
                    target,
                    model,
                    reduced,
                    strategy,
                    seed + iteration,
                    {
                        "original_cumulative": original.costs.model_dump(),
                        "twin_cumulative": twin_costs.model_dump(),
                    },
                )
                records.append(record)
                iteration_report.update(
                    {
                        "counterexample_id": record.counterexample_id,
                        "original_actions": found.actions,
                        "minimized_actions": reduced.minimized.actions,
                        "minimization_status": reduced.status,
                    }
                )
            combined = dict(prior_traces or [])
            for word, outputs in observations_from_database(recorder):
                if word in combined and combined[word] != outputs:
                    raise LoopStop("inconsistent_imported_observations")
                combined[word] = outputs
            traces = list(combined.items())
            # Preserve both full discovery traces and all minimized counterexamples.
            confirmed_traces = []
            for entry in records:
                for case in (entry.minimization.original, entry.minimization.minimized):
                    confirmed_traces.append(
                        (tuple(case.actions), [o.payload for o in case.original])
                    )
            samples, confirmed = encode_samples(traces), encode_samples(confirmed_traces)
            previous = model
            original.phase = f"refinement-learning/{iteration}"
            folder = out / f"revisions/{iteration + 1:03}"
            folder.mkdir()
            model, stats = learn(
                original,
                folder / "model.json",
                seed=seed + iteration,
                walks=refinement_walks,
                walk_length=8,
                samples=samples,
                confirmed=confirmed,
                provenance={
                    "run_id": recorder.run_id,
                    "parent_model_id": model_id(previous),
                    "counterexamples": [entry.counterexample_id for entry in records],
                },
                preserve_checkpoints=True,
            )
            summary["revisions"].append(
                revision_manifest(
                    folder,
                    model,
                    iteration + 1,
                    model_id(previous),
                    stats,
                    [entry.counterexample_id for entry in records],
                )
            )
            original.phase = f"regression-verification/{iteration}"
            with executable_runner(original, folder / "twin.py", twin_costs) as runner:
                regressions = replay_regressions(runner, traces, previous)
            iteration_report["regressions"] = regressions
            iteration_report["original_cost_delta"] = {
                "actions": original.costs.actions - iteration_start.actions,
                "resets": original.costs.resets - iteration_start.resets,
            }
            if regressions["passed"] != regressions["checked"]:
                iteration_report["status"] = "refinement_failed_no_progress"
                corpus.outcome(
                    record,
                    {
                        "status": "unresolved",
                        "new_model_id": model_id(model),
                        "regressions": regressions,
                    },
                )
                completed_records.add(record.counterexample_id)
                summary["status"] = "refinement_failed_no_progress"
                break
            iteration_report["status"] = "resolved"
            summary["resolved_counterexamples"] += 1
            corpus.outcome(
                record,
                {"status": "resolved", "new_model_id": model_id(model), "regressions": regressions},
            )
            completed_records.add(record.counterexample_id)
            write_json(out / "progress.json", summary)
        else:
            summary["status"] = "max_iterations_reached"
    except (LoopStop, BudgetExhausted, OracleFailure, LearningStalled) as exc:
        summary["status"] = (
            str(exc) if isinstance(exc, LoopStop) else type(exc).__name__ + ":" + str(exc)
        )
    except BaseException as exc:
        summary["status"] = "failed:" + type(exc).__name__ + ":" + str(exc)
        raise
    finally:
        for pending in records:
            if pending.counterexample_id not in completed_records:
                corpus.outcome(
                    pending,
                    {"status": "refinement_not_completed", "loop_status": summary["status"]},
                )
        if original is not None:
            original.post(summary["status"])
        if oracle is not None:
            try:
                oracle.close()
            except Exception as exc:
                summary["status"] = "cleanup_failed:" + str(exc)
        summary["original_costs"] = (
            original.costs.model_dump() if original else Costs().model_dump()
        )
        summary["twin_costs"] = twin_costs.model_dump()
        summary["phase_costs"] = phase_costs(recorder)
        cumulative = {
            "actions": summary["phase_costs"].get("initial-learning", {}).get("actions", 0),
            "resets": summary["phase_costs"].get("initial-learning", {}).get("resets", 0),
        }
        for item in summary["iterations"]:
            phases = {
                phase: cost
                for phase, cost in summary["phase_costs"].items()
                if phase.endswith(f"/{item['iteration']}")
            }
            item["phase_costs"] = phases
            for key in ("actions", "resets"):
                cumulative[key] += sum(
                    cost[key] for phase, cost in phases.items() if not phase.startswith("twin:")
                )
            item["cumulative_original_costs"] = dict(cumulative)
        summary["wall_seconds"] = time.monotonic() - started
        for item in summary["iterations"]:
            if item["status"] == "searching":
                item["status"] = summary["status"]
        recorder.artifact("loop_summary", summary)
        recorder.close(summary["status"])
        write_json(out / "summary.json", summary)
    return summary
