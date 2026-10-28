"""Observation-fitted bounded conjunctions and restricted observable balance updates."""

import itertools
import json
from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract
from .typed_runtime import predicate_matches, updated_balance


class Predicate(Contract):
    coefficient: Literal[-1, 0, 1]
    operator: Literal["le", "ge"]
    constant: int


class Update(Contract):
    kind: Literal["keep", "add", "subtract", "constant"]
    value: int = 0


class GuardRule(Contract):
    operation: str
    frozen_context: bool
    guard: list[Predicate]
    updates: list[Update]
    output: dict
    evidence: list[int]
    tested_values: list[int]
    alternatives: list[list[Predicate]] = Field(default_factory=list)
    untested_values: list[int] = Field(default_factory=list)
    boundary_tests: list[dict] = Field(default_factory=list)
    untested_context_values: list[dict] = Field(default_factory=list)


class GuardedModel(Contract):
    schema_version: Literal[2] = 2
    contract: dict
    states: list[list[int | bool]]
    rules: list[GuardRule]
    observations: list[dict]
    provenance: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_states(self):
        from .typed import validate_contract

        validate_contract(self.contract)
        for balance, frozen in self.states:
            if type(balance) is not int or type(frozen) is not bool:
                raise ValueError("Expected strict observable balance/frozen state")
            if (
                not self.contract["balance_domain"][0]
                <= balance
                <= self.contract["balance_domain"][1]
            ):
                raise ValueError("Observable state outside public domain")
        return self


def guard_candidates(positive, negative, bounds):
    """Finite hypothesis-space enumeration, not monotone binary search on target outputs."""
    if not negative:
        return [[]]
    atoms = {}
    for coefficient in (-1, 0, 1):
        pvalues = [r["amount"] + coefficient * r["balance"] for r in positive]
        nvalues = [r["amount"] + coefficient * r["balance"] for r in negative]
        for operator in ("le", "ge"):
            for constant in range(bounds[0], bounds[1] + 1):
                if not all(v <= constant if operator == "le" else v >= constant for v in pvalues):
                    continue
                mask = frozenset(
                    i
                    for i, v in enumerate(nvalues)
                    if not (v <= constant if operator == "le" else v >= constant)
                )
                if not mask:
                    continue
                if operator == "le":
                    ideal = (max(pvalues) + min(nvalues[i] for i in mask)) // 2
                else:
                    ideal = (min(pvalues) + max(nvalues[i] for i in mask) + 1) // 2
                atom = {"coefficient": coefficient, "operator": operator, "constant": constant}
                score = (abs(constant - ideal), abs(coefficient), constant)
                key = coefficient, operator, mask
                if key not in atoms or score < atoms[key][0]:
                    atoms[key] = score, atom, mask
    choices = sorted(atoms.values(), key=lambda x: (x[0], json.dumps(x[1])))[:24]
    complete = frozenset(range(len(negative)))
    solutions = []
    for size in range(1, 4):
        for group in itertools.combinations(choices, size):
            if frozenset().union(*(g[2] for g in group)) != complete:
                continue
            guards = [g[1] for g in group]
            # Prefer fewer terms, then fewer state terms, then midpoint cut proximity.
            score = (
                size,
                sum(abs(g["coefficient"]) for g in guards),
                sum(g[0][0] for g in group),
                json.dumps(guards, sort_keys=True),
            )
            solutions.append((score, guards))
        if solutions:
            break
    if not solutions:
        raise ValueError("Unrepresentable guard under bounded three-term grammar")
    return [s[1] for s in sorted(solutions, key=lambda s: s[0])[:8]]


def fit_model(contract, observations, provenance=None):
    if not observations:
        raise ValueError("Insufficient observations")
    groups, states, seen = defaultdict(list), {(0, False)}, {}
    for index, row in enumerate(observations):
        key = row["balance"], row["frozen"], row["action"]["operation"], row["amount"]
        output = row["output"]
        encoded = json.dumps(output, sort_keys=True)
        if key in seen and seen[key] != encoded:
            raise ValueError("Contradictory observable-state abstraction")
        seen[key] = encoded
        states.add((row["balance"], row["frozen"]))
        states.add((output["balance"], output["frozen"]))
        signature = json.dumps({k: v for k, v in output.items() if k != "balance"}, sort_keys=True)
        groups[(row["action"]["operation"], row["frozen"], signature)].append(index)
    lo, hi = contract["amount_domain"]
    max_balance = contract["balance_domain"][1]
    rules = []
    for (operation, frozen, signature), indices in sorted(groups.items()):
        positive = [observations[i] for i in indices]
        negative = [
            r
            for r in observations
            if r["action"]["operation"] == operation
            and r["frozen"] is frozen
            and json.dumps({k: v for k, v in r["output"].items() if k != "balance"}, sort_keys=True)
            != signature
        ]
        alternatives = guard_candidates(positive, negative, (lo - max_balance, hi + max_balance))
        updates = [{"kind": k, "value": 0} for k in ("keep", "add", "subtract")]
        updates += [
            {"kind": "constant", "value": c}
            for c in range(contract["balance_domain"][0], max_balance + 1)
        ]
        updates = [
            u
            for u in updates
            if all(
                updated_balance(u, r["balance"], r["amount"]) == r["output"]["balance"]
                for r in positive
            )
        ]
        if not updates:
            raise ValueError("Unrepresentable numeric update")
        relevant = [
            (i, r)
            for i, r in enumerate(observations)
            if r["action"]["operation"] == operation and r["frozen"] is frozen
        ]
        tested = sorted({r["amount"] for _, r in relevant})
        rules.append(
            GuardRule(
                operation=operation,
                frozen_context=frozen,
                guard=alternatives[0],
                alternatives=alternatives,
                updates=updates,
                output=json.loads(signature),
                evidence=indices,
                tested_values=tested,
                untested_values=[v for v in range(lo, hi + 1) if v not in tested],
                boundary_tests=[
                    {"observation": i, "balance": r["balance"], "value": r["amount"]}
                    for i, r in relevant
                    if any(
                        abs(r["amount"] + p["coefficient"] * r["balance"] - p["constant"]) <= 1
                        for p in alternatives[0]
                    )
                ],
                untested_context_values=[
                    {
                        "balance": b,
                        "frozen": f,
                        "values": [
                            v
                            for v in range(lo, hi + 1)
                            if not any(r["balance"] == b and r["amount"] == v for _, r in relevant)
                        ],
                    }
                    for b, f in sorted(states)
                    if f is frozen
                ],
            )
        )
    model = GuardedModel(
        contract=contract,
        states=[list(s) for s in sorted(states)],
        rules=rules,
        observations=observations,
        provenance=provenance or {},
    )
    # Every emitted rule must satisfy all positive and exclude all competing observations.
    for row in observations:
        matches = [
            r
            for r in rules
            if r.operation == row["action"]["operation"]
            and r.frozen_context is row["frozen"]
            and all(
                predicate_matches(p.model_dump(), row["balance"], row["amount"]) for p in r.guard
            )
        ]
        if len(matches) != 1:
            raise ValueError("Inconsistent fitted guard partition")
    return model
