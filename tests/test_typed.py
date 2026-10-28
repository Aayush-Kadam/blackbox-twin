import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from blackbox_twin.contracts import Action, Observation, QueryBudget
from blackbox_twin.differential import DifferentialRunner, compare_traces
from blackbox_twin.guards import GuardedModel, fit_model, guard_candidates
from blackbox_twin.m5 import frozen_inputs, make_target, train
from blackbox_twin.oracle import BudgetExhausted, ProcessOracle, Session
from blackbox_twin.planner_oracles import ReplayCacheSUL
from blackbox_twin.storage import Recorder
from blackbox_twin.synthesis import generate_twin
from blackbox_twin.typed import ArgumentSchema, action_key, intern, validate_action, word_keys
from blackbox_twin.typed_learning import adaptive_candidates, amount_action, shrink_typed
from blackbox_twin.typed_runtime import guarded_step

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "examples/typed_wallet/contract.json").read_text())


@pytest.mark.parametrize(
    "value,error",
    [
        (True, "invalid_arguments"),
        (None, "invalid_arguments"),
        (1.0, "invalid_arguments"),
        ("1", "invalid_arguments"),
        (9, "out_of_domain"),
        (-9, "out_of_domain"),
        (0, None),
        (-8, None),
        (8, None),
    ],
)
def test_strict_integer_schema(value, error):
    assert validate_action(amount_action("deposit", value), CONTRACT) == error


def test_boolean_enum_optional_null_and_unknown_schemas():
    contract = {
        "schema_version": 1,
        "operations": {
            "set": {
                "enabled": {"kind": "boolean"},
                "mode": {"kind": "enum", "values": ["a", "b"]},
                "optional": {
                    "kind": "integer",
                    "minimum": 0,
                    "maximum": 1,
                    "optional": True,
                    "nullable": True,
                },
            }
        },
    }
    action = Action(operation="set", arguments={"enabled": True, "mode": "a"})
    assert validate_action(action, contract) is None
    action.arguments["optional"] = None
    assert validate_action(action, contract) is None
    action.arguments["enabled"] = 1
    assert validate_action(action, contract) == "invalid_arguments"
    action.arguments["enabled"] = True
    action.arguments["mode"] = "c"
    assert validate_action(action, contract) == "invalid_arguments"
    with pytest.raises(ValueError):
        ArgumentSchema(kind="integer", minimum=4, maximum=2)
    with pytest.raises(ValueError):
        ArgumentSchema(kind="object")


def test_action_identity_and_serialization_are_type_sensitive():
    left = Action(operation="op", arguments={"n": 1, "flag": True})
    right = Action(operation="op", arguments={"flag": True, "n": 1})
    assert action_key(left) == action_key(right)
    assert Action.model_validate_json(left.model_dump_json()) == left
    assert action_key(amount_action("deposit", True)) != action_key(amount_action("deposit", 1))
    assert action_key(left, "v1") != action_key(left, "v2")


@contextmanager
def physical_session(tmp_path, script=None, budget=100):
    recorder = Recorder(tmp_path / "test.sqlite", {})
    oracle = ProcessOracle(script or ROOT / "fixtures/targets/typed_wallet_process.py")
    session = Session(oracle, make_target("unit-wallet"), QueryBudget(max_actions=budget), recorder)
    try:
        yield session
    finally:
        session.post()
        oracle.close()
        recorder.close("closed")


def test_typed_cache_and_physical_costs(tmp_path):
    with physical_session(tmp_path, budget=2) as session:
        sul = ReplayCacheSUL(session)
        integer = intern(session.target, amount_action("deposit", 1))
        boolean = intern(session.target, amount_action("deposit", True))
        assert sul.query((integer,)) != sul.query((boolean,))
        assert sul.query((integer,))
        assert session.costs.actions == 2 and session.costs.resets == 2
        two = intern(session.target, amount_action("deposit", 2))
        with pytest.raises(BudgetExhausted):
            sul.query((two,))
        assert session.costs.actions == 2


def test_target_error_state_reset_and_boundaries(tmp_path):
    with physical_session(tmp_path) as session:
        actions = [
            amount_action("deposit", 3),
            amount_action("withdraw", 4),
            Action(operation="freeze"),
            amount_action("deposit", 1),
            Action(operation="unfreeze"),
            amount_action("deposit", 1),
            amount_action("deposit", 1),
            amount_action("withdraw", 3),
        ]
        outputs = session.trace(word_keys(session.target, actions))
        assert outputs[0].payload["balance"] == 3
        assert outputs[1].payload["error"] == "transaction_limit"
        assert outputs[3].payload["error"] == "frozen"
        assert outputs[5].payload["balance"] == 4
        assert outputs[6].payload["error"] == "capacity"
        assert outputs[7].payload["balance"] == 1
        reset = session.trace(word_keys(session.target, [Action(operation="get_balance")]))
        assert reset[0].payload == {"status": "ok", "balance": 0, "frozen": False}


@pytest.fixture(scope="module")
def fitted():
    rows = []
    for balance in range(5):
        for frozen in (False, True):
            for operation in ("deposit", "withdraw"):
                for amount in (-8, -1, 0, 1, 3, 4, 5, 8):
                    error, after = None, balance
                    if amount <= 0:
                        error = "invalid_amount"
                    elif frozen:
                        error = "frozen"
                    elif amount > 3:
                        error = "transaction_limit"
                    elif operation == "deposit" and balance + amount > 4:
                        error = "capacity"
                    elif operation == "withdraw" and amount > balance:
                        error = "insufficient"
                    else:
                        after += amount if operation == "deposit" else -amount
                    output = {
                        "status": "error" if error else "ok",
                        "balance": after,
                        "frozen": frozen,
                    }
                    if error:
                        output["error"] = error
                    rows.append(
                        {
                            "balance": balance,
                            "frozen": frozen,
                            "amount": amount,
                            "action": amount_action(operation, amount).model_dump(),
                            "output": output,
                        }
                    )
    return fit_model(CONTRACT, rows)


def test_real_guard_and_update_generalization(fitted):
    model = fitted.model_dump()
    assert all(r["amount"] != 2 for r in model["observations"])
    _, output = guarded_step(model, (0, False), amount_action("deposit", 2).model_dump())
    assert output == {"status": "ok", "balance": 2, "frozen": False}
    _, output = guarded_step(model, (3, False), amount_action("deposit", 2).model_dump())
    assert output["error"] == "capacity" and output["balance"] == 3
    _, output = guarded_step(model, (3, False), amount_action("withdraw", 2).model_dump())
    assert output["status"] == "ok" and output["balance"] == 1
    assert any(p.coefficient != 0 for r in fitted.rules for p in r.guard)


def test_guard_model_version_serialization_and_evidence(fitted):
    restored = GuardedModel.model_validate_json(fitted.model_dump_json())
    assert restored == fitted
    assert all(r.evidence and r.alternatives for r in restored.rules)
    assert all(2 in r.untested_values for r in restored.rules)
    invalid = restored.model_dump()
    invalid["schema_version"] = 99
    with pytest.raises(ValueError):
        GuardedModel.model_validate(invalid)
    invalid = restored.model_dump()
    invalid["rules"][0]["guard"][0]["operator"] = "eval"
    with pytest.raises(ValueError):
        GuardedModel.model_validate(invalid)


def test_ambiguous_missing_regions_and_updates_are_unsupported(fitted):
    model = fitted.model_dump()
    model["rules"] = []
    state, output = guarded_step(model, (0, False), amount_action("deposit", 2).model_dump())
    assert state is None and output["bbt_unsupported"]
    assert guarded_step(model, state, amount_action("deposit", 1).model_dump())[1][
        "bbt_unsupported"
    ]
    model = fitted.model_dump()
    for rule in model["rules"]:
        if rule["operation"] == "deposit" and rule["output"].get("status") == "ok":
            rule["updates"] = [{"kind": "add"}, {"kind": "keep"}]
    assert guarded_step(model, (0, False), amount_action("deposit", 2).model_dump())[1][
        "bbt_unsupported"
    ]


def test_contradictions_and_unsupported_updates_fail_closed(fitted):
    data = [dict(r) for r in fitted.observations]
    data.append({**data[0], "output": {**data[0]["output"], "balance": 1}})
    with pytest.raises(ValueError, match="Contradictory"):
        fit_model(CONTRACT, data)
    with pytest.raises(ValueError, match="Insufficient"):
        fit_model(CONTRACT, [])


def test_adaptive_boundary_selection_is_disjoint_from_reserved(fitted):
    accesses = {(0, False): [], (3, False): []}
    proposals = adaptive_candidates(fitted, accesses, set(CONTRACT["reserved_evaluation_values"]))
    assert all(p[5] not in CONTRACT["reserved_evaluation_values"] for p in proposals)
    assert proposals == adaptive_candidates(
        fitted, accesses, set(CONTRACT["reserved_evaluation_values"])
    )


def test_standalone_twin_and_differential_numeric_fidelity(tmp_path, fitted):
    script = tmp_path / "standalone.py"
    generate_twin(fitted, script)
    assert "blackbox_twin" not in script.read_text()
    with physical_session(tmp_path, script) as session:
        actions = [amount_action("deposit", 2), amount_action("withdraw", 1)]
        outputs = session.trace(word_keys(session.target, actions))
        assert outputs[0].payload["balance"] == 2 and outputs[1].payload["balance"] == 1
    result = compare_traces(
        ["typed"], [Observation(payload={"balance": 2})], [Observation(payload={"balance": 3})]
    )
    assert result.is_mismatch and result.divergent_paths == ["/balance"]


def test_frozen_evaluation_input_groups_are_separate():
    cases = frozen_inputs(CONTRACT)
    assert cases == frozen_inputs(CONTRACT)
    for case in cases:
        allowed = (
            CONTRACT["fixed_grid"]
            if case["category"] == "seen"
            else CONTRACT["reserved_evaluation_values"]
        )
        assert all(
            a["arguments"].get("amount") in allowed for a in case["actions"] if a["arguments"]
        )


def test_actual_training_never_reads_oracle_or_evaluation(tmp_path, monkeypatch):
    script = ROOT / "fixtures/targets/typed_wallet_process.py"
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.resolve() == script.resolve() or path.name in {
            "m5-variants.json",
            "frozen-inputs.json",
        }:
            raise AssertionError("Learner attempted hidden source/config/evaluation read")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    result = train(CONTRACT, script, tmp_path / "run", "adaptive")
    assert result["status"] == "completed"
    assert result["counterexamples"]
    assert all(r["status"] == "agreement" for r in result["counterexample_replays"])
    assert result["regressions"]["passed"] == result["regressions"]["tested"]
    assert result["costs"]["actions"] <= 5000
    evidence = json.loads((tmp_path / "run/counterexample.json").read_text())
    assert evidence["shrinking"]["value_attempts"]


def test_nonconvex_behavior_is_not_forced_into_a_guard():
    with pytest.raises(ValueError, match="Unrepresentable guard"):
        guard_candidates(
            [{"balance": 0, "amount": 1}, {"balance": 0, "amount": 3}],
            [{"balance": 0, "amount": 2}],
            (-12, 12),
        )


def test_argument_shrinking_preserves_state_dependencies(tmp_path):
    mutated = tmp_path / "mutant.py"
    source = (ROOT / "fixtures/targets/typed_wallet_process.py").read_text()
    source = source.replace(
        'balance -= arguments["amount"]',
        'balance -= arguments["amount"]\n'
        "                if balance == 2:\n"
        "                    balance = 1",
    )
    mutated.write_text(source)
    original_dir, twin_dir = tmp_path / "original", tmp_path / "twin"
    original_dir.mkdir()
    twin_dir.mkdir()
    with physical_session(original_dir) as original, physical_session(twin_dir, mutated) as twin:
        twin.target = original.target
        runner = DifferentialRunner(original, twin)
        word = word_keys(
            original.target,
            [
                Action(operation="get_balance"),
                amount_action("deposit", 3),
                amount_action("withdraw", 1),
            ],
        )
        first = runner.run(word)
        assert first.is_mismatch
        reduced, _ = shrink_typed(runner, first, CONTRACT)
        assert reduced.is_mismatch and len(reduced.actions) == 2
        actions = [original.target.actions[k] for k in reduced.actions]
        assert [a.operation for a in actions] == ["deposit", "withdraw"]
        assert reduced.original[reduced.first_divergence].payload["status"] == "ok"
