"""Exact JSON differential testing of independently executed processes."""

from typing import Literal

from pydantic import Field, JsonValue

from .contracts import Contract, Observation
from .oracle import BudgetExhausted, OracleFailure


class Comparison(Contract):
    schema_version: Literal[1] = 1
    actions: list[str]
    status: str
    first_divergence: int | None = None
    divergent_paths: list[str] = Field(default_factory=list)
    original: list[Observation] = Field(default_factory=list)
    twin: list[Observation] = Field(default_factory=list)
    raw_original: list[dict[str, JsonValue]] = Field(default_factory=list)
    raw_twin: list[dict[str, JsonValue]] = Field(default_factory=list)
    failure_side: str | None = None
    failure_stage: str | None = None
    detail: str | None = None
    normalization: Literal["identity-json-v1"] = "identity-json-v1"

    @property
    def is_mismatch(self):
        return self.status in {
            "output_disagreement",
            "error_code_disagreement",
            "structural_disagreement",
            "sequence_length_disagreement",
        }


def json_differences(left, right, path=""):
    """Return JSON pointers; numeric lexical formatting is outside the contract."""
    numeric = type(left) in (int, float) and type(right) in (int, float)
    if type(left) is not type(right) and not numeric:
        return [path], True
    if isinstance(left, dict):
        paths, structural = [], False
        for key in sorted(left.keys() | right.keys()):
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in left or key not in right:
                paths.append(pointer)
                structural = True
            else:
                nested, changed = json_differences(left[key], right[key], pointer)
                paths.extend(nested)
                structural |= changed
        return paths, structural
    if isinstance(left, list):
        paths = [path] if len(left) != len(right) else []
        structural = bool(paths)
        for index, (a, b) in enumerate(zip(left, right, strict=False)):
            nested, changed = json_differences(a, b, path + f"/{index}")
            paths.extend(nested)
            structural |= changed
        return paths, structural
    return ([path] if left != right else []), False


def compare_traces(word, original, twin):
    result = Comparison(
        actions=list(word),
        status="agreement",
        original=original,
        twin=twin,
        raw_original=[o.payload for o in original],
        raw_twin=[o.payload for o in twin],
    )
    for index, (left, right) in enumerate(zip(original, twin, strict=False)):
        paths, structural = json_differences(left.payload, right.payload)
        if right.payload.get("bbt_unsupported") is True and paths:
            result.status, result.first_divergence = "unsupported_twin", index
            return result
        if paths:
            result.first_divergence, result.divergent_paths = index, paths
            if structural:
                result.status = "structural_disagreement"
            elif left.payload.get("error") != right.payload.get("error"):
                result.status = "error_code_disagreement"
            else:
                result.status = "output_disagreement"
            return result
    if len(original) != len(twin):
        result.status = "sequence_length_disagreement"
        result.first_divergence = min(len(original), len(twin))
        result.divergent_paths = [""]
    return result


def failure_kind(exc, stage):
    if isinstance(exc, BudgetExhausted):
        return "budget_exhausted"
    text = str(exc)
    if "timeout" in text:
        return "timeout"
    if "process_eof" in text or "closed_process" in text:
        return "crash"
    if stage == "reset":
        return "reset_failure"
    return "infrastructure_failure"


class DifferentialRunner:
    def __init__(self, original, twin):
        if original.target.actions != twin.target.actions:
            raise ValueError("Different action contracts")
        self.original, self.twin = original, twin

    def run(self, word):
        if self.twin.phase.startswith("twin:"):
            self.twin.phase = "twin:" + self.original.phase
        if any(symbol not in self.original.target.actions for symbol in word):
            raise ValueError("Unsupported action symbol")
        outputs = {"original": [], "twin": []}
        result = None
        for side, session in (("original", self.original), ("twin", self.twin)):
            stage = "reset"
            try:
                session.pre()
                stage = "step"
                for symbol in word:
                    outputs[side].append(session.step(symbol))
                session.post()
            except (OracleFailure, BudgetExhausted) as exc:
                session.post("failed")
                result = Comparison(
                    actions=list(word),
                    status=failure_kind(exc, stage),
                    failure_side=side,
                    failure_stage=stage,
                    detail=str(exc),
                    original=outputs["original"],
                    twin=outputs["twin"],
                    raw_original=[o.payload for o in outputs["original"]],
                    raw_twin=[o.payload for o in outputs["twin"]],
                )
                break
        if result is None:
            result = compare_traces(word, outputs["original"], outputs["twin"])
        self.original.recorder.artifact("comparison", result.model_dump())
        return result
