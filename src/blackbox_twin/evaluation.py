"""Evaluation reads a frozen model; its outputs never feed back into learning."""

import random
import sqlite3

from .contracts import BehavioralModel


def sampled_evaluate(
    session,
    model: BehavioralModel,
    count=100,
    seed=2027,
    minimum_length=9,
    maximum_length=20,
    excluded=(),
):
    rng = random.Random(seed)
    forbidden = set(map(tuple, excluded))
    selected = set()
    exact = steps = matching_steps = error_steps = matching_errors = 0
    mismatches = []
    alphabet = list(model.actions)
    attempts = 0
    while len(selected) < count:
        attempts += 1
        if attempts > count * 100 + 100:
            raise ValueError("Cannot construct enough distinct held-out sequences")
        word = tuple(
            rng.choice(alphabet) for _ in range(rng.randint(minimum_length, maximum_length))
        )
        if word in forbidden or word in selected:
            continue
        selected.add(word)
        observed = session.trace(word)
        predicted = model.predict(word)
        same = observed == predicted
        exact += same
        steps += len(word)
        for left, right in zip(observed, predicted, strict=True):
            matching_steps += left == right
            if "error" in left.payload:
                error_steps += 1
                matching_errors += left == right
        if not same:
            mismatches.append(
                {
                    "actions": list(word),
                    "observed": [o.model_dump() for o in observed],
                    "predicted": [o.model_dump() for o in predicted],
                }
            )
    return {
        "protocol": "distinct unseen full sequences; fixed finite alphabet; exact JSON",
        "seed": seed,
        "count": count,
        "minimum_length": minimum_length,
        "maximum_length": maximum_length,
        "trace_matches": exact,
        "trace_match_rate": exact / count,
        "steps": steps,
        "step_matches": matching_steps,
        "step_match_rate": matching_steps / steps,
        "target_error_steps": error_steps,
        "error_response_match_rate": matching_errors / error_steps if error_steps else None,
        "unsupported_input_rate": 0.0,
        "unsupported_rate_scope": "in-alphabet samples only",
        "equivalence_proven": False,
        "mismatches": mismatches,
        "costs": session.costs.model_dump(),
    }


def training_words(database):
    import json

    database = database.resolve(strict=True)
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        return [
            tuple(json.loads(row[0]))
            for row in db.execute(
                "SELECT actions FROM experiments WHERE phase IN ('training','reset-check')"
            )
        ]
