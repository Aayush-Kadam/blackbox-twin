"""Bounded typed experiments on the existing physical Session and M3 differential pipeline."""

import json
from pathlib import Path

from .contracts import Action
from .counterexamples import minimize
from .defaults import learning_options
from .guards import fit_model
from .learning import learn
from .oracle import BudgetExhausted
from .synthesis import generate_twin
from .typed import decode_word, intern, word_keys
from .typed_runtime import guarded_step, predicate_matches, validation_error


def amount_action(operation, value):
    return Action(operation=operation, arguments={"amount": value})


def grid_actions(contract):
    return [
        amount_action(op, v) for op in ("deposit", "withdraw") for v in contract["fixed_grid"]
    ] + [Action(operation=op) for op in ("get_balance", "freeze", "unfreeze")]


def observations(session, contract):
    rows, accesses, known = [], {(0, False): []}, {}
    db = session.recorder.db
    for (experiment,) in db.execute("SELECT id FROM experiments ORDER BY rowid").fetchall():
        state, prefix = (0, False), []
        for request, response, status in db.execute(
            "SELECT request,response,status FROM events WHERE experiment_id=? AND kind='action' "
            "ORDER BY id",
            (experiment,),
        ).fetchall():
            if status != "ok":
                break
            action = json.loads(request)
            output = json.loads(response)["payload"]
            if type(output.get("balance")) is not int or type(output.get("frozen")) is not bool:
                raise ValueError("Unsupported observable-state output")
            if validation_error(action, contract) is None:
                key = state, json.dumps(action, sort_keys=True)
                encoded = json.dumps(output, sort_keys=True)
                if key in known and known[key] != encoded:
                    raise ValueError("Contradictory observations or insufficient observable state")
                if key not in known:
                    rows.append(
                        {
                            "balance": state[0],
                            "frozen": state[1],
                            "action": action,
                            "amount": action["arguments"].get("amount", 0),
                            "output": output,
                            "access": list(prefix),
                            "experiment": experiment,
                        }
                    )
                    known[key] = encoded
            prefix.append(action)
            state = output["balance"], output["frozen"]
            accesses.setdefault(state, list(prefix))
    return rows, accesses


def probe(session, access, action):
    word = [Action.model_validate(a) for a in access] + [action]
    return session.trace(word_keys(session.target, word))


def initialize(session, contract, folder: Path, seed=5101, equivalence_factory=None):
    folder.mkdir(parents=True)
    for action in grid_actions(contract):
        intern(session.target, action)
    session.phase = "initial-state-learning"
    session.verify_reset()
    physical_limit = session.budget.max_actions
    session.budget.max_actions = min(1000, physical_limit)
    status = "completed_sampled_search"
    try:
        options = learning_options(walks=1, walk_length=3)
        if equivalence_factory is not None:
            options["equivalence_factory"] = equivalence_factory
        learn(
            session,
            folder / "finite-model.json",
            seed=seed,
            **options,
        )
    except BudgetExhausted as exc:
        if str(exc) != "physical_action_budget":
            raise
        status = "initial_phase_action_ceiling"
    finally:
        session.budget.max_actions = physical_limit
        session.post(status)
    # Complete fixed-grid observations in discovered observable contexts, equally for both methods.
    session.phase = "fixed-grid-state-cover"
    tested = set()
    while True:
        rows, accesses = observations(session, contract)
        present = {
            (r["balance"], r["frozen"], json.dumps(r["action"], sort_keys=True)) for r in rows
        }
        pending = [
            (state, access, action)
            for state, access in sorted(accesses.items())
            for action in grid_actions(contract)
            if (state[0], state[1], json.dumps(action.model_dump(), sort_keys=True)) not in present
            and (state, action.model_dump_json()) not in tested
        ]
        if not pending:
            return {"status": status, "observations": len(rows), "states": len(accesses)}
        state, access, action = pending[0]
        tested.add((state, action.model_dump_json()))
        probe(session, access, action)


def save_model(session, contract, folder, revision):
    rows, accesses = observations(session, contract)
    model = fit_model(
        contract,
        rows,
        {
            "revision": revision,
            "method": "bounded observable-state guard fitting; not general RA learning",
            "equivalence_proven": False,
        },
    )
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "model.json").write_text(model.model_dump_json(indent=2), encoding="utf-8")
    generate_twin(model, folder / "twin.py")
    session.recorder.artifact("guarded_model", model.model_dump())
    return model, accesses


def adaptive_candidates(model, accesses, reserved):
    rows, contract = model.observations, model.contract
    seen = {(r["balance"], r["frozen"], r["action"]["operation"], r["amount"]) for r in rows}
    encoded = model.model_dump()
    candidates = []
    lo, hi = contract["amount_domain"]
    for state, access in sorted(accesses.items()):
        for op in ("deposit", "withdraw"):
            rules = [r for r in model.rules if r.operation == op and r.frozen_context is state[1]]
            for value in range(lo, hi + 1):
                if value in reserved or (*state, op, value) in seen:
                    continue
                differences, near = 0, 0
                for rule in rules:
                    predictions = {
                        all(predicate_matches(p.model_dump(), state[0], value) for p in alternative)
                        for alternative in rule.alternatives
                    }
                    differences += len(predictions) > 1
                    near += any(
                        abs(value + p.coefficient * state[0] - p.constant) <= 1 for p in rule.guard
                    )
                _, output = guarded_step(encoded, state, amount_action(op, value).model_dump())
                score = 20 * bool(output.get("bbt_unsupported")) + 5 * differences + near
                if score:
                    candidates.append((score, value > 0, -abs(value), state, op, value, access))
    return sorted(candidates, reverse=True)


def choose_boundary_experiments(session, model, accesses, limit=20):
    candidates = adaptive_candidates(
        model, accesses, set(model.contract["reserved_evaluation_values"])
    )
    selected = candidates[:limit]
    for score, _, _, state, operation, value, access in selected:
        session.recorder.artifact(
            "typed_probe_decision",
            {
                "context": list(state),
                "access": access,
                "operation": operation,
                "value": value,
                "score": score,
                "reason": "guard disagreement, uncovered region, or adjacent boundary",
                "selection": (
                    "bounded model prediction enumeration; no oracle monotonicity assumption"
                ),
            },
        )
        session.phase = "boundary-refinement"
        probe(session, access, amount_action(operation, value))
    return len(selected)


def same_semantics(comparison, original):
    if not comparison.is_mismatch or comparison.divergent_paths != original.divergent_paths:
        return False
    a = comparison.original[comparison.first_divergence].payload
    b = original.original[original.first_divergence].payload
    return (a.get("status"), a.get("error")) == (b.get("status"), b.get("error"))


def shrink_typed(runner, comparison, contract):
    """Reuse M3 ddmin with a semantic rejection filter, then bounded replayed value shrinking."""

    class SemanticRunner:
        original = runner.original

        def run(self, word):
            result = runner.run(word)
            if result.is_mismatch and not same_semantics(result, comparison):
                return result.model_copy(update={"status": "agreement"})
            return result

    minimized = minimize(SemanticRunner(), comparison, max_actions=200, max_attempts=24)
    current = minimized.minimized or comparison
    attempts = []
    for index, action in enumerate(decode_word(runner.original.target, current.actions)):
        if "amount" not in action.arguments:
            continue
        value = action.arguments["amount"]
        options = [
            v
            for v in range(contract["amount_domain"][0], contract["amount_domain"][1] + 1)
            if abs(v) < abs(value) and v not in contract["reserved_evaluation_values"]
        ]
        for candidate in sorted(options, key=lambda v: (abs(v), v))[:8]:
            actions = decode_word(runner.original.target, current.actions)
            actions[index] = amount_action(action.operation, candidate)
            tested = runner.run(word_keys(runner.original.target, actions))
            attempts.append({"value": candidate, "status": tested.status})
            if same_semantics(tested, comparison):
                current = tested
                break
    return current, {
        "sequence_minimization": minimized.model_dump(),
        "value_attempts": attempts,
        "claim": "bounded local reduction preserving target outcome class and fields",
    }
