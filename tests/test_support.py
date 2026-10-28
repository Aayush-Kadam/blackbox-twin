import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from blackbox_twin.contracts import QueryBudget
from blackbox_twin.m5 import make_target
from blackbox_twin.m51 import (
    merge_observations,
    metrics,
    resolving_probe,
    shortest_access,
    train_hardened,
)
from blackbox_twin.oracle import BudgetExhausted, ProcessOracle, Session
from blackbox_twin.storage import Recorder
from blackbox_twin.support import SupportedModel, cell_key, compile_support, version_space
from blackbox_twin.support_runtime import supported_step
from blackbox_twin.synthesis import generate_twin
from blackbox_twin.typed_learning import amount_action, probe

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "examples/typed_wallet/contract.json").read_text())


def row(balance, amount, following, error=None, operation="deposit"):
    output = {"status": "error" if error else "ok", "balance": following, "frozen": False}
    if error:
        output["error"] = error
    return {
        "balance": balance,
        "frozen": False,
        "amount": amount,
        "action": amount_action(operation, amount).model_dump(),
        "output": output,
        "access": [],
    }


@pytest.fixture
def sparse():
    return compile_support(
        CONTRACT, [row(0, -8, 0, "bad"), row(0, 0, 0, "bad"), row(0, 1, 1), row(0, 4, 0, "limit")]
    )


def execute(model, requests, tmp_path):
    script = tmp_path / "standalone.py"
    generate_twin(model, script)
    process = subprocess.run(
        [sys.executable, "-I", "-S", str(script), "--explain"],
        input="\n".join(json.dumps(a) for a in requests) + "\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=15,
        cwd=tmp_path,
    )
    assert not process.stderr
    return [json.loads(line) for line in process.stdout.splitlines()]


def test_all_feasible_threshold_cuts_are_preserved():
    domain = [(0, v) for v in range(5)]
    space = version_space({(0, 1)}, {(0, 4)}, domain, (-4, 4))
    predictions = {bool(mask & (1 << 2)) for mask, _ in space["witnesses"]}
    assert predictions == {True, False}
    assert space["may"] & (1 << 2) and not space["must"] & (1 << 2)


def test_observed_fallback_and_supported_interpolation(sparse):
    observed = sparse.cells[cell_key(0, False, "deposit", 1)]
    inferred = sparse.cells[cell_key(0, False, "deposit", -4)]
    ambiguous = sparse.cells[cell_key(0, False, "deposit", 2)]
    assert observed.status == "OBSERVED" and observed.observation_indices
    assert inferred.status == "INFERRED_SUPPORTED" and inferred.output["error"] == "bad"
    assert ambiguous.status == "AMBIGUOUS" and ambiguous.output is None


def test_support_metadata_has_stable_provenance_and_serializes(sparse):
    loaded = SupportedModel.model_validate_json(sparse.model_dump_json())
    assert loaded == sparse
    assert all(r["rule_id"] and r["evidence"] and r["support_regions"] for r in loaded.rules)
    assert all(r["candidate_partition"]["functions"] > 0 for r in loaded.rules)
    assert compile_support(CONTRACT, sparse.observations).model_id == sparse.model_id


def test_unknown_transition_poisons_until_reset_standalone(sparse, tmp_path):
    outputs = execute(
        sparse,
        [
            amount_action("deposit", 2).model_dump(),
            amount_action("deposit", 1).model_dump(),
            {"control": "reset"},
            amount_action("deposit", 1).model_dump(),
        ],
        tmp_path,
    )
    assert outputs[0]["support"]["status"] == "AMBIGUOUS"
    assert outputs[1]["support"]["status"] == "UNSUPPORTED"
    assert outputs[1]["output"]["reason"] == "unknown_state_until_reset"
    assert outputs[3]["support"]["status"] == "OBSERVED"
    assert outputs[3]["output"]["balance"] == 1


def test_missing_operation_context_is_unsupported_not_known_target_error(sparse, tmp_path):
    results = execute(
        sparse,
        [amount_action("withdraw", 1).model_dump(), amount_action("deposit", 1).model_dump()],
        tmp_path,
    )
    assert results[0]["support"]["status"] == "UNSUPPORTED"
    assert results[0]["output"]["bbt_unsupported"]
    assert results[1]["output"]["reason"] == "unknown_state_until_reset"


@pytest.mark.parametrize(
    "value,error",
    [(True, "invalid_arguments"), (None, "invalid_arguments"), (999999, "out_of_domain")],
)
def test_public_validation_is_distinct_from_twin_refusal(sparse, tmp_path, value, error):
    results = execute(
        sparse,
        [amount_action("deposit", value).model_dump(), amount_action("deposit", 1).model_dump()],
        tmp_path,
    )
    assert results[0]["output"]["error"] == error
    assert results[0]["support"]["reason"] == "public_validation_contract"
    assert not results[0]["output"].get("bbt_unsupported")
    assert results[1]["support"]["status"] == "OBSERVED"


def test_unobserved_control_state_is_unsupported(sparse, tmp_path):
    _, output, support = supported_step(
        sparse.model_dump(), (0, True), amount_action("deposit", 1).model_dump()
    )
    assert output["bbt_unsupported"] and support["status"] == "UNSUPPORTED"
    sequence = execute(
        sparse,
        [
            amount_action("deposit", -4).model_dump(),
            amount_action("deposit", 1).model_dump(),
            amount_action("deposit", -4).model_dump(),
        ],
        tmp_path,
    )
    assert sequence[0]["support"]["status"] == "INFERRED_SUPPORTED"
    assert sequence[1]["support"]["status"] == "OBSERVED"
    assert sequence[2]["support"]["status"] == "AMBIGUOUS"


def test_conflicting_updates_are_not_selected_by_convenience():
    rows = [row(0, x, 0) for x in (-8, 0, 8)]
    rows += [row(1, 0, 1, operation="withdraw")]
    model = compile_support(CONTRACT, rows)
    cell = model.cells[cell_key(1, False, "deposit", 0)]
    assert cell.status == "AMBIGUOUS"
    assert {o["balance"] for o in cell.candidate_outputs} == {0, 1}


def test_contradictions_and_nonconvex_class_fail_closed(sparse):
    contradictory = sparse.observations + [row(0, 1, 0)]
    with pytest.raises(ValueError, match="Contradictory"):
        compile_support(CONTRACT, contradictory)
    nonconvex = compile_support(CONTRACT, [row(0, 1, 0), row(0, 3, 0), row(0, 2, 0, "hole")])
    assert any(r["candidate_partition"]["functions"] == 0 for r in nonconvex.rules)
    assert nonconvex.cells[cell_key(0, False, "deposit", 4)].status == "UNSUPPORTED"
    assert nonconvex.cells[cell_key(0, False, "deposit", 1)].status == "OBSERVED"


def test_ambiguity_probes_respect_reserved_values(sparse):
    reserved = set(range(-8, 9)) - {2}
    choice = resolving_probe(sparse, {(0, False): []}, reserved, random.Random(9))
    assert choice[4].arguments["amount"] == 2
    assert choice[0] == 1
    assert resolving_probe(sparse, {(0, False): []}, set(range(-8, 9)), random.Random(9)) is None


def test_new_distinguishing_observation_resolves_only_its_context(sparse):
    rows = merge_observations(sparse.observations, [row(0, 2, 2)])
    model = compile_support(CONTRACT, rows, [{"kind": "probe", "key": "deposit(2)@0"}])
    assert model.cells[cell_key(0, False, "deposit", 2)].status == "OBSERVED"
    assert model.cells[cell_key(1, False, "deposit", 2)].status != "OBSERVED"
    assert all(r["refinement_history"] for r in model.rules)


def test_coverage_does_not_turn_abstention_into_accuracy():
    cases = [{"category": "unseen", "actions": [amount_action("deposit", 2).model_dump()]}]
    expected = [[{"balance": 2, "status": "ok", "frozen": False}]]
    predicted = [[{"bbt_unsupported": True, "support_status": "AMBIGUOUS"}]]
    result = metrics(cases, expected, predicted, [[{"status": "AMBIGUOUS"}]])["groups"]["unseen"]
    assert result["prediction_coverage"] == result["trace_fidelity"] == 0
    assert result["conditional_accuracy"] is None and result["false_supported_rate"] is None
    assert result["abstention_rate"] == 1


def test_shortest_access_is_real_observed_transition_path():
    rows = [row(0, 1, 1), row(1, 1, 2)]
    assert len(shortest_access(rows)[(2, False)]) == 2


def test_invalid_state_and_empty_evidence_rejected():
    with pytest.raises(ValueError, match="Insufficient"):
        compile_support(CONTRACT, [])
    with pytest.raises(ValueError, match="Invalid observable state"):
        compile_support(CONTRACT, [row(0, 1, 100)])


def test_physical_distinguishing_probe_is_charged_and_resolves(tmp_path, sparse):
    recorder = Recorder(tmp_path / "physical.sqlite", {})
    oracle = ProcessOracle(ROOT / "fixtures/targets/typed_wallet_process.py")
    session = Session(oracle, make_target("probe-unit"), QueryBudget(max_actions=1), recorder)
    try:
        choice = resolving_probe(
            sparse, {(0, False): []}, set(range(-8, 9)) - {2}, random.Random(4)
        )
        result = probe(session, choice[3], choice[4])
        extra = row(0, 2, result[-1].payload["balance"])
        extra["output"] = result[-1].payload
        model = compile_support(CONTRACT, merge_observations(sparse.observations, [extra]))
        assert model.cells[cell_key(0, False, "deposit", 2)].status == "OBSERVED"
        assert session.costs.actions == session.costs.resets == 1
        with pytest.raises(BudgetExhausted):
            probe(session, [], amount_action("deposit", 1))
        assert session.costs.actions == 1
        outputs = execute(model, [amount_action("deposit", 2).model_dump()], tmp_path)
        assert outputs[0]["support"]["status"] == "OBSERVED"
        assert outputs[0]["output"]["balance"] == 2
    finally:
        session.post()
        oracle.close()
        recorder.close("closed")


def test_zero_resolution_budget_preserves_ambiguity_and_standalone_refusal(tmp_path, monkeypatch):
    target_script = ROOT / "fixtures/targets/typed_wallet_process.py"
    original_open = Path.open

    def guarded(path, *args, **kwargs):
        if path.resolve() == target_script.resolve() or path.name in {
            "generation.json",
            "frozen-inputs.json",
            "m5-1-fresh.json",
        }:
            raise AssertionError("Hardened inference attempted a hidden/evaluation file read")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    contract = json.loads(json.dumps(CONTRACT))
    contract["reserved_evaluation_values"] = [-7, -5, -3, 3, 6, 7]
    receipt = train_hardened(
        contract,
        ROOT / "fixtures/targets/typed_wallet_process.py",
        tmp_path / "zero-probes",
        max_probes=0,
    )
    assert receipt["stop"] == "probe_cap" and not receipt["probes"]
    model = SupportedModel.model_validate_json(
        (tmp_path / "zero-probes" / receipt["model"]).read_text()
    )
    assert any(c.status == "AMBIGUOUS" for c in model.cells.values())
    result = execute(model, [amount_action("deposit", 2).model_dump()], tmp_path)
    assert result[0]["support"]["status"] == "AMBIGUOUS"
    assert receipt["regressions"]["passed"] == receipt["regressions"]["tested"]


def test_update_disagreement_is_refused_by_standalone(tmp_path):
    rows = [row(0, x, 0) for x in (-8, 0, 8)]
    rows += [row(0, 1, 1, operation="withdraw"), row(1, 0, 1, operation="withdraw")]
    model = compile_support(CONTRACT, rows)
    result = execute(
        model,
        [amount_action("withdraw", 1).model_dump(), amount_action("deposit", 0).model_dump()],
        tmp_path,
    )
    assert result[0]["support"]["status"] == "OBSERVED"
    assert result[1]["support"]["status"] == "AMBIGUOUS"
    assert result[1]["output"]["bbt_unsupported"]
