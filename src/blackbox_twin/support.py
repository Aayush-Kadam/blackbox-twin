"""Exact bounded guard version spaces and evidence-supported finite applicability regions."""

import hashlib
import itertools
import json
from collections import defaultdict
from typing import Literal

from pydantic import Field

from .contracts import Contract
from .typed import validate_contract
from .typed_runtime import predicate_matches, updated_balance, validation_error


class SupportCell(Contract):
    status: Literal["OBSERVED", "INFERRED_SUPPORTED", "AMBIGUOUS", "UNSUPPORTED"]
    output: dict | None = None
    rule_ids: list[str] = Field(default_factory=list)
    observation_indices: list[int] = Field(default_factory=list)
    reason: str
    candidate_outputs: list[dict] = Field(default_factory=list)


class SupportedModel(Contract):
    schema_version: Literal[3] = 3
    model_id: str
    contract: dict
    states: list[list[int | bool]]
    observations: list[dict]
    rules: list[dict]
    cells: dict[str, SupportCell]
    provenance: dict


def cell_key(balance, frozen, operation, amount):
    return json.dumps([balance, frozen, operation, amount], separators=(",", ":"))


def version_space(positive, negative, domain, bounds):
    """Enumerate ALL distinct domain functions with <=3 allowed atoms; never cap candidates."""
    full = (1 << len(domain)) - 1
    positive_mask = sum(1 << i for i, p in enumerate(domain) if p in positive)
    negative_mask = sum(1 << i for i, p in enumerate(domain) if p in negative)
    atoms = {}
    for coefficient, operator, constant in itertools.product(
        (-1, 0, 1), ("le", "ge"), range(bounds[0], bounds[1] + 1)
    ):
        predicate = dict(coefficient=coefficient, operator=operator, constant=constant)
        mask = sum(1 << i for i, (b, x) in enumerate(domain) if predicate_matches(predicate, b, x))
        if mask & positive_mask == positive_mask:
            atoms.setdefault(mask, predicate)
    masks = list(atoms)
    solutions = {}
    if not negative_mask:
        solutions[full] = []
    for size in range(1, 4):
        for group in itertools.combinations(masks, size):
            mask = full
            for part in group:
                mask &= part
            if not mask & negative_mask:
                solutions.setdefault(mask, [atoms[m] for m in group])
    may, must = 0, full
    for mask in solutions:
        may |= mask
        must &= mask
    return {
        "functions": len(solutions),
        "may": may,
        "must": must if solutions else 0,
        "witnesses": [(mask, guard) for mask, guard in solutions.items()],
    }


def compile_support(contract, observations, history=None):
    validate_contract(contract)
    if not observations:
        raise ValueError("Insufficient observations")
    groups, seen, states = defaultdict(list), {}, {(0, False)}
    for index, row in enumerate(observations):
        if validation_error(row["action"], contract) is not None:
            raise ValueError("Observation outside public typed schema")
        key = (row["balance"], row["frozen"], json.dumps(row["action"], sort_keys=True))
        output = row["output"]
        if key in seen and seen[key] != output:
            raise ValueError("Contradictory observable-state evidence")
        seen[key] = output
        for b, f in [(row["balance"], row["frozen"]), (output["balance"], output["frozen"])]:
            if (
                type(b) is not int
                or type(f) is not bool
                or not contract["balance_domain"][0] <= b <= contract["balance_domain"][1]
            ):
                raise ValueError("Invalid observable state")
            states.add((b, f))
        signature = json.dumps({k: v for k, v in output.items() if k != "balance"}, sort_keys=True)
        groups[(row["action"]["operation"], row["frozen"], signature)].append(index)
    lo, hi = contract["amount_domain"]
    blo, bhi = contract["balance_domain"]
    domains = {}
    for op, schema in contract["operations"].items():
        if schema and (set(schema) != {"amount"} or schema["amount"]["kind"] != "integer"):
            raise ValueError(
                "Support inference is restricted to wallet integer/zero-argument schemas"
            )
        domains[op] = [
            (b, x) for b in range(blo, bhi + 1) for x in (range(lo, hi + 1) if schema else [0])
        ]
    rules, spaces = [], {}
    for (op, frozen, signature), indices in sorted(groups.items()):
        relevant = [
            (i, r)
            for i, r in enumerate(observations)
            if r["action"]["operation"] == op and r["frozen"] is frozen
        ]
        positive = {(observations[i]["balance"], observations[i]["amount"]) for i in indices}
        negative = {(r["balance"], r["amount"]) for i, r in relevant if i not in indices}
        space = version_space(positive, negative, domains[op], (lo - bhi, hi + bhi))
        identifier = hashlib.sha256(json.dumps([op, frozen, signature]).encode()).hexdigest()[:16]
        updates = [{"kind": k, "value": 0} for k in ("keep", "add", "subtract")]
        updates += [{"kind": "constant", "value": c} for c in range(blo, bhi + 1)]
        updates = [
            u
            for u in updates
            if all(
                updated_balance(u, observations[i]["balance"], observations[i]["amount"])
                == observations[i]["output"]["balance"]
                for i in indices
            )
        ]
        if not updates:
            raise ValueError("Unrepresentable arithmetic update")
        spaces[identifier] = space
        rules.append(
            {
                "rule_id": identifier,
                "model_version": 3,
                "operation": op,
                "frozen_context": frozen,
                "output": json.loads(signature),
                "updates": updates,
                "evidence": indices,
                "boundary_observations": [i for i, _ in relevant],
                "contradictions": [],
                "refinement_history": history or [],
                "candidate_partition": {
                    "domain": [list(point) for point in domains[op]],
                    "functions": space["functions"],
                    "may_mask": hex(space["may"]),
                    "must_mask": hex(space["must"]),
                    "grammar": "all conjunctions of zero to three x+k*b inequalities, k=-1/0/1",
                },
                "witness_guards": [g for _, g in space["witnesses"][:2]],
                "applicability": "OBSERVED context or full candidate-space output/update consensus",
            }
        )
    cells = {}
    for b, f in sorted(states):
        for op, domain in domains.items():
            for index, (balance, amount) in enumerate(domain):
                if balance != b:
                    continue
                relevant_rules = [
                    r for r in rules if r["operation"] == op and r["frozen_context"] is f
                ]
                direct = [
                    i
                    for i, row in enumerate(observations)
                    if row["balance"] == b
                    and row["frozen"] is f
                    and row["action"]["operation"] == op
                    and row["amount"] == amount
                ]
                if direct:
                    cell = SupportCell(
                        status="OBSERVED",
                        output=observations[direct[0]]["output"],
                        observation_indices=direct,
                        reason="same concrete observable state/action",
                        rule_ids=[
                            r["rule_id"] for r in relevant_rules if direct[0] in r["evidence"]
                        ],
                    )
                else:
                    possible, mandatory, outputs = [], [], {}
                    empty_space = any(not spaces[r["rule_id"]]["functions"] for r in relevant_rules)
                    for rule in relevant_rules:
                        space = spaces[rule["rule_id"]]
                        if space["may"] & (1 << index):
                            possible.append(rule["rule_id"])
                            for update in rule["updates"]:
                                output = {
                                    **rule["output"],
                                    "balance": updated_balance(update, b, amount),
                                }
                                outputs[json.dumps(output, sort_keys=True)] = output
                        if space["must"] & (1 << index):
                            mandatory.append(rule["rule_id"])
                    status, output, reason = "AMBIGUOUS", None, "guard_or_update_disagreement"
                    if empty_space or not possible:
                        status, reason = "UNSUPPORTED", "empty_version_space_or_no_response_class"
                    elif len(possible) == len(mandatory) == len(outputs) == 1:
                        output = next(iter(outputs.values()))
                        if (output["balance"], output["frozen"]) in states:
                            status, reason = (
                                "INFERRED_SUPPORTED",
                                "complete_bounded_version_space_consensus",
                            )
                        else:
                            output, status, reason = None, "UNSUPPORTED", "unobserved_next_state"
                    cell = SupportCell(
                        status=status,
                        output=output,
                        reason=reason,
                        rule_ids=possible,
                        candidate_outputs=list(outputs.values()),
                    )
                cells[cell_key(b, f, op, amount)] = cell
    for rule in rules:
        rule["support_regions"] = {
            status: [
                key
                for key, cell in cells.items()
                if rule["rule_id"] in cell.rule_ids and cell.status == status
            ]
            for status in ("OBSERVED", "INFERRED_SUPPORTED", "AMBIGUOUS", "UNSUPPORTED")
        }
        rule["evidence_status"] = (
            "INFERRED_SUPPORTED" if rule["support_regions"]["INFERRED_SUPPORTED"] else "OBSERVED"
        )
        rule["known_counterexamples"] = history or []
    semantic_rows = [
        {k: r[k] for k in ("balance", "frozen", "action", "output")} for r in observations
    ]
    identifier = hashlib.sha256(
        json.dumps([contract, semantic_rows], sort_keys=True).encode()
    ).hexdigest()
    return SupportedModel(
        model_id=identifier,
        contract=contract,
        states=[list(s) for s in sorted(states)],
        observations=observations,
        rules=rules,
        cells=cells,
        provenance={
            "status_semantics": "evidence metadata, not certainty outside the declared grammar",
            "assumptions": [
                "deterministic reset",
                "observable balance/frozen sufficient state",
                "discovered response vocabulary",
                "three-term bounded guard grammar",
                "restricted updates",
            ],
            "class_spaces": (
                "independent overapproximation; overlaps/holes are not forced into a partition"
            ),
            "refinement_history": history or [],
        },
    )
