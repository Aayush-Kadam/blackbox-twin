"""Local M5 orchestration. Evaluator configuration is never an inference argument."""

import hashlib
import json
import random
import time
from contextlib import contextmanager
from pathlib import Path

from .benchmark import benchmark_recorder
from .contracts import Action, QueryBudget, Target
from .differential import DifferentialRunner
from .oracle import BudgetExhausted, ProcessOracle, Session
from .refinement import phase_costs
from .storage import utc_now
from .typed import decode_word, validate_contract, word_keys
from .typed_learning import (
    amount_action,
    choose_boundary_experiments,
    initialize,
    observations,
    save_model,
    shrink_typed,
)


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def make_target(identifier):
    return Target(
        target_id=identifier,
        version="1",
        executable="oracle.py",
        authorization="owned-local-fixture",
        actions={},
    )


@contextmanager
def twin_runner(original, script, folder):
    recorder = benchmark_recorder(folder / "twin-observations.sqlite", {"side": "twin"})
    oracle = ProcessOracle(script)
    twin = Session(
        oracle,
        original.target,
        QueryBudget(
            max_actions=30000, max_resets=5000, total_seconds=120.0, max_sequence_length=40
        ),
        recorder,
        "twin:typed-diff",
    )
    try:
        yield DifferentialRunner(original, twin)
    finally:
        twin.post()
        oracle.close()
        recorder.artifact("costs", twin.costs.model_dump())
        recorder.close("closed")


def discover(runner, model, accesses, contract, limit=32):
    known = {
        (r["balance"], r["frozen"], r["action"]["operation"], r["amount"])
        for r in model.observations
    }
    attempts = 0
    for state, access in sorted(accesses.items()):
        for operation in ("deposit", "withdraw"):
            for value in range(*[contract["amount_domain"][0], contract["amount_domain"][1] + 1]):
                if (
                    value in contract["reserved_evaluation_values"]
                    or (*state, operation, value) in known
                ):
                    continue
                if attempts >= limit:
                    return None
                actions = [Action.model_validate(a) for a in access] + [
                    amount_action(operation, value)
                ]
                runner.original.phase = "differential-search"
                result = runner.run(word_keys(runner.original.target, actions))
                attempts += 1
                if result.is_mismatch:
                    return result
    return None


def train(contract, oracle_script, folder, method):
    folder.mkdir(parents=True)
    recorder = benchmark_recorder(
        folder / "observations.sqlite",
        {"contract": contract, "method": method, "budget": contract["training_budget"]},
    )
    oracle = ProcessOracle(oracle_script)
    session = Session(
        oracle,
        make_target("typed-wallet"),
        QueryBudget(**contract["training_budget"], max_sequence_length=40),
        recorder,
    )
    started, status, revision = time.perf_counter(), "failed", 0
    summary = {"method": method, "counterexamples": [], "refinement_iterations": 0}
    try:
        summary["initial_learning"] = initialize(session, contract, folder / "finite-baseline")
        model, accesses = save_model(session, contract, folder / "revision-000", revision)
        first = None
        if method == "adaptive":
            with twin_runner(session, folder / "revision-000/twin.py", folder) as runner:
                first = discover(runner, model, accesses, contract)
                if first:
                    session.phase = "counterexample-minimization"
                    reduced, evidence = shrink_typed(runner, first, contract)
                    write(
                        folder / "counterexample.json",
                        {
                            "discovery": first.model_dump(),
                            "minimized": reduced.model_dump(),
                            "actions": [
                                a.model_dump() for a in decode_word(session.target, reduced.actions)
                            ],
                            "shrinking": evidence,
                        },
                    )
                    summary["counterexamples"].append(reduced.actions)
            for _ in range(3):
                revision += 1
                session.phase = "guard-hypothesis-discrimination"
                model, accesses = save_model(
                    session, contract, folder / f"revision-{revision:03}", revision
                )
                if not choose_boundary_experiments(session, model, accesses, limit=16):
                    break
            revision += 1
            session.phase = "relearning"
            model, accesses = save_model(
                session, contract, folder / f"revision-{revision:03}", revision
            )
            summary["refinement_iterations"] = revision
            with twin_runner(session, folder / f"revision-{revision:03}/twin.py", folder) as runner:
                session.phase = "counterexample-replay"
                summary["counterexample_replays"] = [
                    runner.run(word).model_dump() for word in summary["counterexamples"]
                ]
                # Every distinct observed contextual action is reexecuted against both processes.
                rows, _ = observations(session, contract)
                regression_words = list(
                    dict.fromkeys(
                        tuple(
                            word_keys(
                                session.target,
                                [Action.model_validate(a) for a in r["access"]]
                                + [Action.model_validate(r["action"])],
                            )
                        )
                        for r in rows
                    )
                )
                session.phase = "regression-replay"
                regressions = [runner.run(word) for word in regression_words]
                summary["regressions"] = {
                    "tested": len(regressions),
                    "passed": sum(r.status == "agreement" for r in regressions),
                    "failures": [r.model_dump() for r in regressions if r.status != "agreement"],
                }
        summary["final_revision"] = revision
        summary["model"] = f"revision-{revision:03}/model.json"
        summary["twin"] = f"revision-{revision:03}/twin.py"
        status = "completed"
    except BudgetExhausted as exc:
        status = "budget_exhausted:" + str(exc)
    except BaseException as exc:
        summary["failure"] = type(exc).__name__ + ":" + str(exc)
        raise
    finally:
        session.post(status)
        oracle.close()
        summary.update(
            status=status,
            costs=session.costs.model_dump(),
            phase_costs=phase_costs(recorder),
            wall_seconds=time.perf_counter() - started,
        )
        recorder.artifact("typed_training", summary)
        recorder.close(status)
        write(folder / "training.json", summary)
    return summary


def frozen_inputs(contract):
    rng = random.Random(contract["evaluation"]["sequence_seed"])
    cases = []
    for category, values in (
        ("seen", contract["fixed_grid"]),
        ("unseen", contract["reserved_evaluation_values"]),
    ):
        for _ in range(contract["evaluation"]["sequences"] // 2):
            actions = [amount_action("deposit", rng.choice(values))]
            for _ in range(rng.randint(*contract["evaluation"]["length"]) - 1):
                op = rng.choice(list(contract["operations"]))
                actions.append(
                    amount_action(op, rng.choice(values))
                    if op in {"deposit", "withdraw"}
                    else Action(operation=op)
                )
            cases.append({"category": category, "actions": [a.model_dump() for a in actions]})
    return cases


def evaluator_cases(cap):
    # Ground-truth-owned contexts; called only after training, never passed to learner.
    cases = []
    for balance in range(cap + 1):
        for frozen in (False, True):
            prefix = [amount_action("deposit", 1) for _ in range(balance)]
            if frozen:
                prefix.append(Action(operation="freeze"))
            for operation in ("deposit", "withdraw"):
                for value in range(-8, 9):
                    actions = prefix + [
                        amount_action(operation, value),
                        Action(operation="get_balance"),
                    ]
                    cases.append(
                        {
                            "category": "exhaustive",
                            "context": [balance, frozen],
                            "operation": operation,
                            "value": value,
                            "probe_index": len(prefix),
                            "actions": [a.model_dump() for a in actions],
                        }
                    )
            invalid = [
                {},
                {"amount": None},
                {"amount": True},
                {"amount": 1.0},
                {"amount": "1"},
                {"amount": 999999},
                {"amount": 1, "extra": True},
            ]
            for arguments in invalid:
                cases.append(
                    {
                        "category": "validation",
                        "actions": [
                            a.model_dump()
                            for a in prefix
                            + [
                                Action(operation="deposit", arguments=arguments),
                                Action(operation="get_balance"),
                            ]
                        ],
                    }
                )
    return cases


def acquire_reference(script, contract, cases, folder):
    folder.mkdir()
    recorder = benchmark_recorder(
        folder / "observations.sqlite", {"phase": "post-training-evaluation"}
    )
    oracle = ProcessOracle(script)
    session = Session(
        oracle,
        make_target("evaluation"),
        QueryBudget(
            max_actions=20000, max_resets=5000, total_seconds=120.0, max_sequence_length=40
        ),
        recorder,
        "held-out-evaluation",
    )
    try:
        outputs = [
            [
                o.payload
                for o in session.trace(
                    word_keys(session.target, [Action.model_validate(a) for a in c["actions"]])
                )
            ]
            for c in cases
        ]
        receipt = {"outputs": outputs, "costs": session.costs.model_dump()}
        write(folder / "references.json", receipt)
        return outputs
    finally:
        session.post()
        oracle.close()
        recorder.close("completed")


def score(script, contract, cases, truth, folder):
    outputs = acquire_reference(script, contract, cases, folder)
    groups, guard_points = {}, []
    for case, expected, actual in zip(cases, truth, outputs, strict=True):
        group = groups.setdefault(
            case["category"],
            {"traces": 0, "trace_matches": 0, "outputs": 0, "output_matches": 0, "unsupported": 0},
        )
        group["traces"] += 1
        group["trace_matches"] += actual == expected
        group["outputs"] += len(expected)
        group["output_matches"] += sum(a == b for a, b in zip(expected, actual, strict=True))
        group["unsupported"] += sum(o.get("bbt_unsupported") is True for o in actual)
        if case["category"] == "exhaustive":
            index = case["probe_index"]
            guard_points.append(
                {
                    "context": case["context"],
                    "operation": case["operation"],
                    "value": case["value"],
                    "target_accept": expected[index].get("status") == "ok",
                    "twin_accept": actual[index].get("status") == "ok",
                    "target_class": expected[index].get("error", "ok"),
                    "twin_class": actual[index].get(
                        "error", "ok" if actual[index].get("status") == "ok" else "unsupported"
                    ),
                }
            )
    for group in groups.values():
        group["trace_fidelity"] = group["trace_matches"] / group["traces"]
        group["output_fidelity"] = group["output_matches"] / group["outputs"]
        group["unsupported_frequency"] = group["unsupported"] / group["outputs"]
    tp = sum(p["target_accept"] and p["twin_accept"] for p in guard_points)
    predicted = sum(p["twin_accept"] for p in guard_points)
    positive = sum(p["target_accept"] for p in guard_points)
    boundaries = {side: set() for side in ("target", "twin")}
    for left, right in zip(guard_points, guard_points[1:], strict=False):
        if left["context"] == right["context"] and left["operation"] == right["operation"]:
            for side in boundaries:
                if left[side + "_class"] != right[side + "_class"]:
                    boundaries[side].add((*left["context"], left["operation"], left["value"]))
    result = {
        "groups": groups,
        "guard_population": len(guard_points),
        "guard_precision": tp / predicted if predicted else None,
        "guard_recall": tp / positive if positive else None,
        "boundaries": {
            "target": len(boundaries["target"]),
            "twin": len(boundaries["twin"]),
            "matched": len(boundaries["target"] & boundaries["twin"]),
            "exact": boundaries["target"] == boundaries["twin"],
        },
    }
    write(folder / "evaluation.json", result)
    return result


def run_demo(project, out, development=False):
    out.mkdir(parents=True)
    contract = validate_contract(
        json.loads((project / "examples/typed_wallet/contract.json").read_text())
    )
    freeze = json.loads((project / "evidence/m5-contract-freeze.json").read_text())
    for name, digest in freeze["files"].items():
        if hashlib.sha256((project / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen contract/fixture changed: " + name)
    variants = json.loads((project / "benchmarks/manifests/m5-variants.json").read_text())
    configs = variants["development" if development else "evaluation"]
    inputs = frozen_inputs(contract)
    write(out / "frozen-inputs.json", inputs)
    write(
        out / "protocol.json",
        {
            "contract": contract,
            "freeze": freeze,
            "label": "development" if development else "evaluation",
            "frozen_at": utc_now(),
            "source_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob("*.py")
            },
        },
    )
    summary = {}
    for name, config in configs.items():
        pair = out / name
        pair.mkdir()
        # Launcher-only configuration injection, never visible to train().
        source = (project / "fixtures/targets/typed_wallet_process.py").read_text()
        source = source.replace("CAP = 4", f"CAP = {config['cap']}")
        source = source.replace("LIMIT = 3", f"LIMIT = {config['limit']}")
        script = pair / "oracle.py"
        script.write_text(source, encoding="utf-8")
        write(
            pair / "target-fingerprint.json",
            {"config": config, "sha256": hashlib.sha256(script.read_bytes()).hexdigest()},
        )
        training = {
            method: train(contract, script, pair / method, method)
            for method in ("fixed-grid", "adaptive")
        }
        cases = inputs + evaluator_cases(config["cap"])
        write(pair / "evaluation-cases.json", cases)
        truth = acquire_reference(script, contract, cases, pair / "evaluation-reference")
        evaluation = {
            method: score(
                pair / method / result["twin"],
                contract,
                cases,
                truth,
                pair / ("evaluation-" + method),
            )
            for method, result in training.items()
            if "twin" in result
        }
        summary[name] = {"training": training, "evaluation": evaluation}
        write(out / "summary.json", summary)
    return summary
