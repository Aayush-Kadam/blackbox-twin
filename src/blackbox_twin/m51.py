"""Bounded evidence-policy hardening, paired fresh evaluation, and diagnostic regressions."""

import hashlib
import json
import random
import time
from collections import Counter, deque
from pathlib import Path

from .benchmark import benchmark_recorder
from .contracts import Action, QueryBudget
from .m5 import (
    acquire_reference,
    evaluator_cases,
    frozen_inputs,
    make_target,
    train,
    twin_runner,
    write,
)
from .oracle import ProcessOracle, Session
from .refinement import phase_costs
from .storage import utc_now
from .support import compile_support
from .support_runtime import supported_step
from .synthesis import generate_twin
from .typed import word_keys
from .typed_learning import amount_action, grid_actions, observations, probe
from .typed_runtime import guarded_step


def shortest_access(rows):
    access, queue = {(0, False): []}, deque([(0, False)])
    while queue:
        before = queue.popleft()
        for row in rows:
            if (row["balance"], row["frozen"]) != before:
                continue
            after = row["output"]["balance"], row["output"]["frozen"]
            if after not in access:
                access[after] = access[before] + [row["action"]]
                queue.append(after)
    return access


def merge_observations(old, new):
    merged, seen = [], {}
    for row in old + new:
        key = row["balance"], row["frozen"], json.dumps(row["action"], sort_keys=True)
        if key in seen and seen[key] != row["output"]:
            raise ValueError("Contradictory observations after refinement")
        if key not in seen:
            merged.append(row)
            seen[key] = row["output"]
    return merged


def resolving_probe(model, accesses, reserved, rng):
    choices = []
    for key, cell in model.cells.items():
        if cell.status != "AMBIGUOUS":
            continue
        b, f, op, value = json.loads(key)
        if value in reserved or (b, f) not in accesses:
            continue
        access = accesses[(b, f)]
        choices.append(
            (
                len(access) + 1,
                rng.random(),
                key,
                access,
                amount_action(op, value)
                if model.contract["operations"][op]
                else Action(operation=op),
            )
        )
    return min(choices, key=lambda x: (x[0], x[1], x[2])) if choices else None


def train_hardened(contract, script, folder, seed=71101, max_probes=12):
    folder.mkdir(parents=True)
    started = time.perf_counter()
    legacy = train(contract, script, folder / "legacy-seed", "fixed-grid")
    if legacy["status"] != "completed":
        raise ValueError("Legacy seed failed; retained receipt: " + legacy["status"])
    seed_model = json.loads((folder / "legacy-seed" / legacy["model"]).read_text())
    recorder = benchmark_recorder(
        folder / "observations.sqlite", {"method": "hardened", "seed": seed}
    )
    session = Session(
        ProcessOracle(script),
        make_target("hardened-wallet"),
        QueryBudget(
            max_actions=contract["training_budget"]["max_actions"] - legacy["costs"]["actions"],
            max_resets=contract["training_budget"]["max_resets"] - legacy["costs"]["resets"],
            total_seconds=max(
                0.001,
                contract["training_budget"]["total_seconds"] - (time.perf_counter() - started),
            ),
            max_sequence_length=40,
        ),
        recorder,
        "ambiguity-reset-validation",
    )
    rows, rng, history = (
        seed_model["observations"],
        random.Random(seed),
        [{"kind": "common_StatePrefix_fixed_grid_seed", "source": "legacy-seed/training.json"}],
    )
    summary = {"method": "hardened", "seed_training": legacy, "probes": [], "status": "failed"}
    try:
        for action in grid_actions(contract):
            word_keys(session.target, [action])
        session.verify_reset()
        for revision in range(max_probes + 1):
            fresh, _ = observations(session, contract)
            rows = merge_observations(rows, fresh)
            model = compile_support(contract, rows, history)
            destination = folder / f"revision-{revision:03}"
            destination.mkdir()
            write(destination / "model.json", model.model_dump())
            generate_twin(model, destination / "twin.py")
            recorder.artifact(
                "support_model_ref",
                {
                    "model_id": model.model_id,
                    "revision": revision,
                    "file": f"revision-{revision:03}/model.json",
                },
            )
            accesses = shortest_access(rows)
            choice = resolving_probe(
                model, accesses, set(contract["reserved_evaluation_values"]), rng
            )
            if choice is None or revision == max_probes:
                summary["stop"] = (
                    "no_permitted_distinguishing_probe" if choice is None else "probe_cap"
                )
                break
            cost, _, key, access, action = choice
            # Check the next atomic reset/access experiment; no padding of leftover budget.
            if (
                session.costs.actions + cost > session.budget.max_actions
                or session.costs.resets >= session.budget.max_resets
            ):
                summary["stop"] = "physical_budget_for_probe_exhausted"
                break
            session.phase = "ambiguity-resolution"
            before_actions = session.costs.actions
            result = probe(session, access, action)
            item = {
                "key": key,
                "access": access,
                "action": action.model_dump(),
                "estimated_actions": cost,
                "actual_actions": session.costs.actions - before_actions,
                "target_output": result[-1].payload,
                "parent_model": model.model_id,
            }
            summary["probes"].append(item)
            history = history + [
                {
                    "kind": "ambiguity_probe",
                    "key": key,
                    "parent_model": model.model_id,
                    "experiment": session.recorder.db.execute(
                        "SELECT id FROM experiments ORDER BY rowid DESC LIMIT 1"
                    ).fetchone()[0],
                }
            ]
        summary.update(
            model=f"revision-{revision:03}/model.json",
            twin=f"revision-{revision:03}/twin.py",
            model_id=model.model_id,
            revisions=revision,
            support_counts=dict(Counter(c.status for c in model.cells.values())),
        )
        with twin_runner(session, destination / "twin.py", folder) as runner:
            session.phase = "support-regression"
            regression_words = list(
                dict.fromkeys(
                    tuple(
                        word_keys(
                            session.target,
                            [Action.model_validate(a) for a in row.get("access", [])]
                            + [Action.model_validate(row["action"])],
                        )
                    )
                    for row in rows
                )
            )
            results = [runner.run(word) for word in regression_words]
            summary["regressions"] = {
                "tested": len(results),
                "passed": sum(r.status == "agreement" for r in results),
                "failures": [r.model_dump() for r in results if r.status != "agreement"],
            }
        summary["status"] = "completed"
    finally:
        session.post(summary["status"])
        session.oracle.close()
        summary["additional_costs"] = session.costs.model_dump()
        summary["costs"] = {
            k: legacy["costs"][k] + session.costs.model_dump()[k] for k in legacy["costs"]
        }
        summary["additional_phase_costs"] = phase_costs(recorder)
        summary["wall_seconds"] = time.perf_counter() - started
        recorder.close(summary["status"])
        write(folder / "training.json", summary)
    return summary


def predict_trace(model, actions):
    state, outputs, statuses = (0, False), [], []
    for action in actions:
        if model["schema_version"] == 3:
            state, output, metadata = supported_step(model, state, action)
        else:
            state, output = guarded_step(model, state, action)
            metadata = {
                "status": "UNSUPPORTED" if output.get("bbt_unsupported") else "LEGACY_CONCRETE"
            }
        outputs.append(output)
        statuses.append(metadata)
    return outputs, statuses


def metrics(cases, truth, outputs, statuses):
    groups, points = {}, []
    for case, expected, actual, metadata in zip(cases, truth, outputs, statuses, strict=True):
        group = groups.setdefault(
            case["category"],
            {
                "traces": 0,
                "exact_traces": 0,
                "concrete_traces": 0,
                "correct_concrete_traces": 0,
                "outputs": 0,
                "exact_outputs": 0,
                "concrete_outputs": 0,
                "correct_concrete_outputs": 0,
                "support_status_counts": {},
            },
        )
        group["traces"] += 1
        group["exact_traces"] += actual == expected
        complete = all(not a.get("bbt_unsupported") for a in actual)
        group["concrete_traces"] += complete
        group["correct_concrete_traces"] += complete and actual == expected
        for a, b, status in zip(actual, expected, metadata, strict=True):
            concrete = not a.get("bbt_unsupported")
            group["outputs"] += 1
            group["exact_outputs"] += a == b
            group["concrete_outputs"] += concrete
            group["correct_concrete_outputs"] += concrete and a == b
            counts = group["support_status_counts"]
            counts[status["status"]] = counts.get(status["status"], 0) + 1
        if case["category"] == "exhaustive":
            index = case["probe_index"]
            points.append(
                (expected[index].get("status") == "ok", actual[index].get("status") == "ok")
            )
    for group in groups.values():
        n, steps, concrete = group["traces"], group["outputs"], group["concrete_outputs"]
        group.update(
            trace_fidelity=group["exact_traces"] / n,
            output_fidelity=group["exact_outputs"] / steps,
            prediction_coverage=concrete / steps,
            abstention_rate=(steps - concrete) / steps,
            conditional_accuracy=group["correct_concrete_outputs"] / concrete if concrete else None,
            false_supported_rate=(concrete - group["correct_concrete_outputs"]) / concrete
            if concrete
            else None,
            sequence_coverage=group["concrete_traces"] / n,
            conditional_trace_accuracy=group["correct_concrete_traces"] / group["concrete_traces"]
            if group["concrete_traces"]
            else None,
        )
    true_positive = sum(a and b for a, b in points)
    predictions, positives = sum(b for _, b in points), sum(a for a, _ in points)
    return {
        "groups": groups,
        "guard_population": len(points),
        "guard_precision": true_positive / predictions if predictions else None,
        "guard_recall": true_positive / positives if positives else None,
    }


def evaluate(script, model, contract, cases, truth, folder):
    outputs = acquire_reference(script, contract, cases, folder)
    metadata = []
    for case, actual in zip(cases, outputs, strict=True):
        predicted, statuses = predict_trace(model, case["actions"])
        if predicted != actual:
            raise ValueError("Standalone and serialized support runtimes disagree")
        metadata.append(statuses)
    result = metrics(cases, truth, outputs, metadata)
    write(folder / "support.json", metadata)
    write(folder / "metrics.json", result)
    return result


def run_fresh(project, out, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    if (
        hashlib.sha256(
            (project / "fixtures/targets/typed_wallet_process.py").read_bytes()
        ).hexdigest()
        != protocol["fixture_sha256"]
    ):
        raise ValueError("Frozen wallet fixture changed")
    for name, digest in protocol["source_sha256"].items():
        if hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen support-policy source changed: " + name)
    out.mkdir(parents=True)
    write(out / "protocol.json", protocol)
    contract = protocol["contract"]
    inputs = frozen_inputs(contract)
    write(out / "frozen-inputs.json", inputs)
    source_root = out / "source-snapshot/blackbox_twin"
    source_root.mkdir(parents=True)
    for name in protocol["source_sha256"]:
        (source_root / name).write_bytes((Path(__file__).parent / name).read_bytes())
    pool = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 3), (3, 4), (4, 1), (4, 4)]
    random.Random(protocol["target_seed"]).shuffle(pool)
    summary = {}
    for index, (cap, limit) in enumerate(pool[:2]):
        pair = out / f"fresh-{index}"
        pair.mkdir()
        source = (project / "fixtures/targets/typed_wallet_process.py").read_text()
        source = source.replace("CAP = 4", f"CAP = {cap}").replace("LIMIT = 3", f"LIMIT = {limit}")
        script = pair / "oracle.py"
        script.write_text(source)
        write(
            pair / "generation.json",
            {"cap": cap, "limit": limit, "sha256": hashlib.sha256(script.read_bytes()).hexdigest()},
        )
        training = {
            method: train(contract, script, pair / method, method)
            for method in ("fixed-grid", "adaptive")
        }
        training["hardened"] = train_hardened(
            contract,
            script,
            pair / "hardened",
            protocol["probe_seed"] + index,
            protocol["max_probes"],
        )
        cases = inputs + evaluator_cases(cap)
        write(pair / "evaluation-cases.json", cases)
        truth = acquire_reference(script, contract, cases, pair / "evaluation-reference")
        evaluation = {}
        for method, receipt in training.items():
            model = json.loads((pair / method / receipt["model"]).read_text())
            evaluation[method] = evaluate(
                pair / method / receipt["twin"],
                model,
                contract,
                cases,
                truth,
                pair / ("evaluation-" + method),
            )
        # Isolate support policy from additional resolution observations (no extra learning calls).
        legacy_model = json.loads((pair / "adaptive" / training["adaptive"]["model"]).read_text())
        policy_only = compile_support(contract, legacy_model["observations"])
        write(pair / "policy-only.json", policy_only.model_dump())
        generate_twin(policy_only, pair / "policy-only.py")
        evaluation["policy-only"] = evaluate(
            pair / "policy-only.py",
            policy_only.model_dump(),
            contract,
            cases,
            truth,
            pair / "evaluation-policy-only",
        )
        summary[f"fresh-{index}"] = {"training": training, "evaluation": evaluation}
        write(out / "summary.json", summary)
    return summary


def freeze_protocol(project, path):
    contract = json.loads((project / "examples/typed_wallet/contract.json").read_text())
    contract["reserved_evaluation_values"] = [-7, -5, -3, 3, 6, 7]
    contract["evaluation"]["sequence_seed"] = 81101
    if path.exists():
        raise ValueError("Protocol already frozen")
    write(
        path,
        {
            "policy_version": "m5.1-complete-bounded-consensus-v1",
            "frozen_at": utc_now(),
            "contract": contract,
            "target_seed": 61101,
            "probe_seed": 71101,
            "underlying_legacy_StatePrefix_seed": 5101,
            "max_probes": 12,
            "training_ceiling_per_arm": 5000,
            "maximum_training_actions": 30000,
            "source_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob("*.py")
            },
            "label": "two-configuration focused M5.1 evaluation, not M6",
            "value_split_revision": "3 withheld, 2 permitted; original M5 split/data untouched",
            "fixture_sha256": hashlib.sha256(
                (project / "fixtures/targets/typed_wallet_process.py").read_bytes()
            ).hexdigest(),
        },
    )
