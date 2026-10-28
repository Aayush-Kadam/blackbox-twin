"""Replay-validated deletion minimization and append-only corpus revisions."""

import hashlib
import json
import time
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, JsonValue

from .contracts import Contract
from .differential import Comparison, json_differences
from .storage import utc_now


class UnsupportedDependency(ValueError):
    pass


def require_finite_actions(target):
    def has_reference(value):
        if isinstance(value, str):
            return value.startswith("@")
        if isinstance(value, dict):
            return any(has_reference(v) for v in value.values())
        if isinstance(value, list):
            return any(has_reference(v) for v in value)
        return False

    if any(has_reference(action.arguments) for action in target.actions.values()):
        raise UnsupportedDependency("Symbolic references need binding semantics; unsupported in M3")


class Minimization(Contract):
    schema_version: Literal[1] = 1
    status: str
    original: Comparison
    minimized: Comparison | None = None
    attempts: int = 0
    attempts_evidence: list[dict[str, JsonValue]] = Field(default_factory=list)
    locally_minimal: bool = False
    physical_actions: int = 0


def minimize(runner, initial: Comparison, max_actions=1000, max_attempts=200, total_seconds=30.0):
    require_finite_actions(runner.original.target)
    if not initial.is_mismatch:
        raise ValueError("Only behavioral mismatches can be minimized")
    if max_actions < 0 or max_attempts < 0 or total_seconds <= 0:
        raise ValueError("Invalid minimization limits")
    result = Minimization(status="budget_exhausted", original=initial)
    started = time.monotonic()
    before = runner.original.costs.actions

    def attempt(word):
        used = runner.original.costs.actions - before
        if (
            used + len(word) > max_actions
            or result.attempts >= max_attempts
            or time.monotonic() - started >= total_seconds
        ):
            return None
        comparison = runner.run(word)
        result.attempts += 1
        result.attempts_evidence.append({"actions": list(word), "status": comparison.status})
        return comparison

    def same_failure(comparison):
        # Preserve mismatch category and divergent field; infrastructure is never a reduction.
        return (
            comparison is not None
            and comparison.is_mismatch
            and comparison.status == initial.status
            and comparison.divergent_paths == initial.divergent_paths
        )

    current = attempt(initial.actions)
    if current is None:
        return result
    if (
        not same_failure(current)
        or json_differences(current.raw_original, initial.raw_original)[0]
        or json_differences(current.raw_twin, initial.raw_twin)[0]
    ):
        result.status = "non_reproducing" if current.status == "agreement" else current.status
        if current.is_mismatch:
            result.status = "non_reproducing"
        result.physical_actions = runner.original.costs.actions - before
        return result
    result.minimized = current
    word, granularity, stopped = list(current.actions), 2, False
    # ddmin complement deletion, followed by a repeated single-deletion fixed point.
    while len(word) >= 2:
        chunk = (len(word) + granularity - 1) // granularity
        reduced = False
        for start in range(0, len(word), chunk):
            candidate = word[:start] + word[start + chunk :]
            tested = attempt(candidate)
            if tested is None:
                stopped = True
                break
            if tested.status not in {
                "agreement",
                "output_disagreement",
                "error_code_disagreement",
                "structural_disagreement",
                "sequence_length_disagreement",
            }:
                result.status, stopped = tested.status, True
                break
            if same_failure(tested):
                word, result.minimized = candidate, tested
                granularity, reduced = max(2, granularity - 1), True
                break
        if stopped:
            break
        if not reduced:
            if granularity >= len(word):
                break
            granularity = min(len(word), granularity * 2)
    changed = True
    while not stopped and changed:
        changed = False
        for index in range(len(word)):
            tested = attempt(word[:index] + word[index + 1 :])
            if tested is None:
                stopped = True
                break
            if tested.status not in {
                "agreement",
                "output_disagreement",
                "error_code_disagreement",
                "structural_disagreement",
                "sequence_length_disagreement",
            }:
                result.status, stopped = tested.status, True
                break
            if same_failure(tested):
                word, result.minimized, changed = tested.actions, tested, True
                break
    if not stopped:
        result.status, result.locally_minimal = "completed", True
    result.physical_actions = runner.original.costs.actions - before
    return result


def model_id(model):
    return hashlib.sha256(model.model_dump_json().encode()).hexdigest()


class CorpusRecord(Contract):
    schema_version: Literal[1] = 1
    counterexample_id: str
    target_id: str
    target_version: str
    model_id: str
    created_at: str
    strategy: str
    seed: int
    minimization: Minimization
    query_costs: dict[str, JsonValue]
    status: str = "confirmed"
    comparison_policy: Literal["identity-json-v1"] = "identity-json-v1"
    replay_metadata: dict[str, JsonValue] = Field(default_factory=dict)


class Corpus:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, target, model, minimized, strategy, seed, costs):
        if minimized.minimized is None or not minimized.minimized.is_mismatch:
            raise ValueError("No replay-confirmed minimized mismatch")
        record = CorpusRecord(
            counterexample_id=str(uuid4()),
            target_id=target.target_id,
            target_version=target.version,
            model_id=model_id(model),
            created_at=utc_now(),
            strategy=strategy,
            seed=seed,
            minimization=minimized,
            query_costs=costs,
            replay_metadata={"reset": target.reset, "fresh_reset_per_candidate": True},
        )
        folder = self.root / record.counterexample_id
        folder.mkdir()
        (folder / "discovery.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def outcome(self, record, outcome):
        folder = self.root / record.counterexample_id
        index = len(list(folder.glob("outcome-*.json")))
        with (folder / f"outcome-{index:03}.json").open("x", encoding="utf-8") as out:
            json.dump({"schema_version": 1, "recorded_at": utc_now(), **outcome}, out, indent=2)

    @staticmethod
    def read(path):
        return CorpusRecord.model_validate_json(Path(path).read_text(encoding="utf-8"))
