"""Frozen paired evaluation, invoked only after learning/refinement has stopped."""

import json
import sqlite3
import time
from pathlib import Path

from .contracts import BehavioralModel, Costs, QueryBudget
from .counterexamples import model_id
from .differential import json_differences
from .experiments import random_sequences
from .oracle import ProcessOracle, Session
from .refinement import LoopStop, executable_runner, phase_costs, write_json
from .storage import Recorder, utc_now
from .synthesis import generate_twin


def freeze_sequences(target, destination, seed=991, count=100, min_length=16, max_length=24):
    if count < 1:
        raise ValueError("Hold-out count must be positive")
    selected, seen = [], set()
    for word in random_sequences(list(target.actions), seed, count * 100, min_length, max_length):
        if word not in seen:
            selected.append(list(word))
            seen.add(word)
        if len(selected) == count:
            break
    if len(selected) != count:
        raise ValueError("Not enough distinct hold-out sequences")
    value = {
        "schema_version": 1,
        "target_id": target.target_id,
        "target_version": target.version,
        "actions": {k: v.model_dump() for k, v in target.actions.items()},
        "seed": seed,
        "created_at": utc_now(),
        "sequences": selected,
    }
    with destination.open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2)
    return value


def read_prior_traces(database, target):
    database = Path(database).resolve(strict=True)
    traces = {}
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        runs = db.execute("SELECT metadata FROM runs").fetchall()
        for (metadata,) in runs:
            known = json.loads(metadata).get("target", {})
            if known.get("target_id") != target.target_id or known.get("version") != target.version:
                raise ValueError("Observation database target identity differs")
        rows = db.execute("SELECT id,actions,phase FROM experiments WHERE status='completed'")
        for exp, encoded, phase in rows.fetchall():
            if phase.startswith("twin:"):
                continue
            if "held-out" in phase:
                raise ValueError("Held-out observations cannot be imported as training evidence")
            word = tuple(json.loads(encoded))
            if any(s not in target.actions for s in word):
                raise ValueError("Observation alphabet differs")
            outputs = [
                json.loads(row[0])["payload"]
                for row in db.execute(
                    "SELECT response FROM events WHERE experiment_id=? AND kind='action' "
                    "AND status='ok' ORDER BY id",
                    (exp,),
                )
            ]
            if word and len(outputs) == len(word):
                if word in traces and traces[word] != outputs:
                    raise ValueError("Contradictory imported observations")
                traces[word] = outputs
    return list(traces.items())


def evaluate_pair(
    target,
    script,
    initial: BehavioralModel,
    refined: BehavioralModel,
    sequence_file,
    training_database,
    out,
    budget: QueryBudget,
):
    dataset = json.loads(Path(sequence_file).read_text(encoding="utf-8"))
    if (
        dataset["schema_version"] != 1
        or dataset["target_id"] != target.target_id
        or dataset["target_version"] != target.version
        or dataset["actions"] != {k: v.model_dump() for k, v in target.actions.items()}
    ):
        raise ValueError("Held-out contract differs")
    words = [tuple(word) for word in dataset["sequences"]]
    if not words or len(set(words)) != len(words):
        raise ValueError("Held-out set must contain distinct nonempty sequences")
    training = {word for word, _ in read_prior_traces(training_database, target)}
    if training.intersection(words):
        raise ValueError("Held-out sequences overlap physical training observations")
    if initial.actions != target.actions or refined.actions != target.actions:
        raise ValueError("Model action contract differs")
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Evaluation output must be empty")
    write_json(out / "frozen-sequences.json", dataset)
    config = {
        "target": target.model_dump(),
        "initial_model_id": model_id(initial),
        "refined_model_id": model_id(refined),
        "budget": budget.model_dump(),
        "seed": dataset["seed"],
        "full_sequence_training_overlap": 0,
    }
    write_json(out / "config.json", config)
    recorder = Recorder(out / "observations.sqlite", config)
    original = None
    twin_costs, scores = Costs(), {}
    reference_traces = {}
    status, started = "failed", time.monotonic()
    try:
        original = Session(ProcessOracle(script), target, budget, recorder, "held-out")
        for label, model in (("initial", initial), ("refined", refined)):
            twin = out / f"{label}-twin.py"
            generate_twin(model, twin)
            original.phase = f"held-out/{label}"
            score = {
                "traces": len(words),
                "trace_matches": 0,
                "steps": 0,
                "step_matches": 0,
                "error_steps": 0,
                "error_matches": 0,
                "unsupported_traces": 0,
            }
            with executable_runner(original, twin, twin_costs) as runner:
                for word in words:
                    comparison = runner.run(word)
                    truth = [o.payload for o in comparison.original]
                    if label == "initial":
                        reference_traces[word] = truth
                    elif json_differences(reference_traces[word], truth)[0]:
                        raise LoopStop("inconsistent_heldout_reference_outputs")
                    if comparison.status not in {
                        "agreement",
                        "output_disagreement",
                        "error_code_disagreement",
                        "structural_disagreement",
                        "sequence_length_disagreement",
                        "unsupported_twin",
                    }:
                        raise LoopStop(comparison.status)
                    score["trace_matches"] += comparison.status == "agreement"
                    score["unsupported_traces"] += comparison.status == "unsupported_twin"
                    for left, right in zip(comparison.original, comparison.twin, strict=True):
                        matches = not json_differences(left.payload, right.payload)[0]
                        score["steps"] += 1
                        score["step_matches"] += matches
                        if "error" in left.payload:
                            score["error_steps"] += 1
                            score["error_matches"] += matches
            score["trace_match_rate"] = score["trace_matches"] / len(words)
            score["step_match_rate"] = score["step_matches"] / score["steps"]
            scores[label] = score
        status = "completed"
    finally:
        if original is not None:
            original.post(status)
            original.oracle.close()
        result = {
            "schema_version": 1,
            "status": status,
            "scores": scores,
            "original_costs": original.costs.model_dump() if original else Costs().model_dump(),
            "twin_costs": twin_costs.model_dump(),
            "phase_costs": phase_costs(recorder),
            "wall_seconds": time.monotonic() - started,
            "equivalence_proven": False,
            "full_sequence_training_overlap": 0,
        }
        recorder.artifact("paired_evaluation", result)
        recorder.close(status)
        write_json(out / "evaluation.json", result)
    return result
