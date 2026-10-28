"""Sequential resumable M6 campaign: frozen targets, physical receipts and independent twins."""

import hashlib
import json
import statistics
import time
from pathlib import Path

from .benchmark import benchmark_recorder
from .contracts import Action, QueryBudget, Target
from .m5 import make_target, write
from .m6_targets import evaluation_inputs, inventory_step, render, wallet_step
from .m6_train import finite_train, typed_train, unsupported_train
from .m51 import metrics, predict_trace
from .oracle import ProcessOracle, Session
from .storage import utc_now
from .typed import word_keys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(folder):
    return {
        p.relative_to(folder).as_posix(): sha(p)
        for p in folder.rglob("*")
        if p.is_file() and p.name != "integrity.json" and "__pycache__" not in p.parts
    }


def verify(folder):
    expected = json.loads((folder / "integrity.json").read_text())
    for name, digest in expected.items():
        if not (folder / name).is_file() or sha(folder / name) != digest:
            raise ValueError("Artifact integrity failure: " + str(folder / name))


def source_hashes():
    return {p.name: sha(p) for p in Path(__file__).parent.glob("*.py")}


def load_protocol(path):
    protocol = json.loads(path.read_text())
    if protocol.get("schema_version") != 1:
        raise ValueError("Unsupported M6 protocol")
    streams = [set(protocol[k]) for k in ("learner_seeds", "training_seeds", "evaluation_seeds")]
    if any(a & b for i, a in enumerate(streams) for b in streams[i + 1 :]):
        raise ValueError("Seed streams overlap")
    if len(protocol["training_seeds"]) < len(protocol["learner_seeds"]):
        raise ValueError("Missing independent training stream seeds")
    if any(b < 1 for v in protocol["budgets"].values() for b in v):
        raise ValueError("Invalid action ceiling")
    return protocol


def acquire(script, cases, folder, label):
    folder.mkdir(parents=True)
    recorder = benchmark_recorder(folder / "observations.sqlite", {"side": label})
    oracle = ProcessOracle(script)
    session = Session(
        oracle,
        make_target(label),
        QueryBudget(
            max_actions=sum(len(c["actions"]) for c in cases),
            max_resets=len(cases),
            max_sequence_length=max(len(c["actions"]) for c in cases),
            total_seconds=120.0,
        ),
        recorder,
        label,
    )
    complete = False
    try:
        outputs = [
            [
                o.payload
                for o in session.trace(
                    word_keys(session.target, [Action.model_validate(a) for a in case["actions"]])
                )
            ]
            for case in cases
        ]
        complete = True
        receipt = {"complete": True, "outputs": outputs, "costs": session.costs.model_dump()}
        write(folder / "receipt.json", receipt)
    finally:
        session.post("completed" if complete else "interrupted")
        oracle.close()
        recorder.close("completed" if complete else "interrupted")
        if not complete:
            write(folder / "receipt.json", {"complete": False, "costs": session.costs.model_dump()})
    write(folder / "integrity.json", fingerprint(folder))
    return receipt


def attempt(folder, runner):
    folder.mkdir(parents=True, exist_ok=True)
    for previous in sorted(folder.glob("attempt-*")):
        receipt = previous / "receipt.json"
        if receipt.exists() and json.loads(receipt.read_text()).get("complete"):
            verify(previous)
            return previous, json.loads(receipt.read_text())
    index = len(list(folder.glob("attempt-*")))
    destination = folder / f"attempt-{index:03}"
    receipt = runner(destination)
    write(destination / "integrity.json", fingerprint(destination))
    return destination, receipt


def model_predictions(model, actions):
    if model["schema_version"] in (2, 3):
        return predict_trace(model, actions)
    inner = model if model["schema_version"] == 1 else model.get("finite")
    state = inner["initial_state"] if inner else None
    mapping = (
        {
            json.dumps(a, sort_keys=True, separators=(",", ":")): k
            for k, a in inner["actions"].items()
        }
        if inner
        else {}
    )
    outputs, support = [], []
    for action in actions:
        symbol = mapping.get(json.dumps(action, sort_keys=True, separators=(",", ":")))
        if state is None or symbol is None:
            state = None
            output = {
                "bbt_unsupported": True,
                "support_status": "UNSUPPORTED",
                "reason": model.get("reason", "outside_learned_alphabet"),
            }
            status = "UNSUPPORTED"
        else:
            edge = inner["transitions"][state][symbol]
            state, output, status = edge["next_state"], edge["output"]["payload"], "LEGACY_CONCRETE"
        outputs.append(output)
        support.append({"status": status})
    return outputs, support


def finite_product(table, model):
    if model["schema_version"] != 1:
        return {"equivalent": False, "reason": "no_finite_model"}
    pending, seen = [(0, model["initial_state"], [])], set()
    while pending:
        original, inferred, prefix = pending.pop()
        if (original, inferred) in seen:
            continue
        seen.add((original, inferred))
        for symbol, (following, output) in table[original].items():
            edge = model["transitions"][inferred][symbol]
            if edge["output"]["payload"] != output:
                return {"equivalent": False, "witness": prefix + [symbol]}
            pending.append((following, edge["next_state"], prefix + [symbol]))
    return {
        "equivalent": True,
        "reachable_product_pairs": len(seen),
        "scope": "known evaluator finite table and fixed alphabet only",
    }


def score(model, cases, truth, actual):
    supports = []
    first_refusals, propagated = 0, 0
    for case, measured in zip(cases, actual, strict=True):
        predicted, metadata = model_predictions(model, case["actions"])
        if predicted != measured:
            raise ValueError("Serialized model and independent executable disagree")
        supports.append(metadata)
        unknown = False
        for output in measured:
            if output.get("bbt_unsupported"):
                propagated += unknown
                first_refusals += not unknown
                unknown = True
    groups = metrics(cases, truth, actual, supports)
    total_cases = [{**case, "category": "all"} for case in cases]
    groups["overall"] = metrics(total_cases, truth, actual, supports)["groups"]["all"]
    groups["unknown_state_cascades"] = {
        "first_refusal_sequences": first_refusals,
        "later_refusals": propagated,
    }
    return groups


def prepare(project, out, protocol):
    wallet = json.loads((project / "examples/typed_wallet/contract.json").read_text())
    wallet["reserved_evaluation_values"] = protocol["reserved_values"]
    for spec, eval_seed in zip(protocol["targets"], protocol["evaluation_seeds"], strict=True):
        folder = out / spec["id"]
        if (folder / "prepared.json").exists():
            verify(folder / "target")
            continue
        (folder / "target").mkdir(parents=True)
        source, target, contract, table = render(project, spec, wallet)
        script = folder / "target/oracle.py"
        if spec["track"] == "A" and spec["family"] == "rare" and spec["variant"] == 0:
            script.write_bytes(
                (project / "evidence/m4-1/target-rare-access/oracle.py").read_bytes()
            )
        else:
            script.write_text(source, encoding="utf-8")
        write(folder / "target/target.json", target.model_dump())
        if contract:
            write(folder / "target/public-contract.json", contract)
        if table:
            write(folder / "target/evaluator-table.json", table)
        cases = evaluation_inputs(spec, target, contract, eval_seed)
        write(folder / "target/inputs.json", cases)
        write(folder / "target/integrity.json", fingerprint(folder / "target"))
        write(
            folder / "prepared.json",
            {
                "frozen_at": utc_now(),
                "target_sha256": sha(script),
                "inputs_sha256": sha(folder / "target/inputs.json"),
            },
        )


def cells_for(spec, protocol):
    count = protocol["finite_seed_count"] if spec["track"] == "A" else protocol["typed_seed_count"]
    methods = protocol["methods"][spec["track"]]
    budgets = (
        [protocol["budgets"]["A"]]
        if spec["track"] == "A"
        else [[b] for b in protocol["budgets"][spec["track"]]]
    )
    return [
        (i, method, ceilings) for i in range(count) for method in methods for ceilings in budgets
    ]


def run_campaign(project, manifest, out, resume=False):
    protocol = load_protocol(manifest)
    if protocol["source_sha256"] != source_hashes():
        raise ValueError("Frozen source changed")
    for name, digest in protocol.get("resources_sha256", {}).items():
        if sha(project / name) != digest:
            raise ValueError("Frozen resource changed: " + name)
    if out.exists():
        if not resume or json.loads((out / "protocol.json").read_text()) != protocol:
            raise ValueError("Use a new output or matching --resume")
    else:
        out.mkdir(parents=True)
        write(out / "protocol.json", protocol)
        snapshot = out / "source-snapshot/blackbox_twin"
        snapshot.mkdir(parents=True)
        for name in protocol["source_sha256"]:
            (snapshot / name).write_bytes((Path(__file__).parent / name).read_bytes())
    prepare(project, out, protocol)
    started = time.perf_counter()
    all_results = []
    for spec in protocol["targets"]:
        folder = out / spec["id"]
        target = Target.model_validate_json((folder / "target/target.json").read_text())
        contract = (
            json.loads((folder / "target/public-contract.json").read_text())
            if spec["track"] != "A"
            else None
        )
        cases = json.loads((folder / "target/inputs.json").read_text())
        completed = []
        for index, method, ceilings in cells_for(spec, protocol):
            cell = folder / f"seed-{index}-{method}-{max(ceilings)}"
            learner_seed, stream_seed = (
                protocol["learner_seeds"][index],
                protocol["training_seeds"][index],
            )

            def train_one(
                destination,
                method=method,
                ceilings=ceilings,
                learner_seed=learner_seed,
                stream_seed=stream_seed,
                folder=folder,
                spec=spec,
                contract=contract,
                target=target,
            ):
                script = folder / "target/oracle.py"
                if spec["track"] == "B":
                    return typed_train(
                        contract,
                        script,
                        destination,
                        max(ceilings),
                        method,
                        learner_seed,
                        stream_seed,
                    )
                if spec["track"] == "C" and method != "fixed-grid":
                    return unsupported_train(
                        destination,
                        max(ceilings),
                        "two_counter_inventory_not_representable_by_wallet_guard_grammar",
                    )
                selected = "aalpy-state-prefix" if spec["track"] == "C" else method
                return finite_train(
                    target.model_copy(deep=True),
                    script,
                    destination,
                    ceilings,
                    selected,
                    learner_seed,
                    stream_seed,
                    concrete=spec["track"] == "C",
                )

            attempt_folder, receipt = attempt(cell / "training", train_one)
            completed.append((cell, attempt_folder, receipt, index, method))
            write(
                out / "progress.json",
                {
                    "completed_evaluated_cells": len(all_results),
                    "current_target_training_cells": len(completed),
                    "current_target": spec["id"],
                    "last_training_status": receipt["status"],
                },
            )
        reference_folder, reference = attempt(
            folder / "reference",
            lambda p, folder=folder, cases=cases: acquire(
                folder / "target/oracle.py", cases, p, "original-evaluation"
            ),
        )
        if spec["track"] != "A":
            step = wallet_step if spec["track"] == "B" else inventory_step
            initial = (0, False) if spec["track"] == "B" else (0, 0)
            for case, outputs in zip(cases, reference["outputs"], strict=True):
                state, expected = initial, []
                for action in case["actions"]:
                    state, output = step(state, action, spec["parameters"], contract)
                    expected.append(output)
                if expected != outputs:
                    raise ValueError("Independent evaluator and fixture disagree")
        for cell, training, receipt, index, method in completed:
            result_path = cell / "result.json"
            if result_path.exists():
                if (
                    sha(result_path)
                    != json.loads((cell / "result-integrity.json").read_text())["sha256"]
                ):
                    raise ValueError("Result integrity failure: " + str(result_path))
                all_results.append(json.loads(result_path.read_text()))
                continue
            points = []
            for point in receipt["points"]:
                prediction_folder, predicted = attempt(
                    cell / f"evaluation-{point['ceiling']}",
                    lambda p, point=point, training=training, cases=cases: acquire(
                        training / point["twin"], cases, p, "twin-evaluation"
                    ),
                )
                model = json.loads((training / point["model"]).read_text())
                measured = score(model, cases, reference["outputs"], predicted["outputs"])
                criterion = (
                    measured["overall"]["trace_fidelity"] >= 0.95
                    and measured["overall"]["prediction_coverage"] >= 0.95
                )
                eligible = receipt["status"] in {"completed", "action_budget"}
                data = {
                    **point,
                    "metrics": measured,
                    "criterion_reached": eligible and criterion,
                    "evaluation_folder": str(prediction_folder.relative_to(out)),
                    "model_bytes": (training / point["model"]).stat().st_size,
                }
                if spec["track"] == "A":
                    data["finite_product"] = finite_product(
                        json.loads((folder / "target/evaluator-table.json").read_text()), model
                    )
                points.append(data)
            result = {
                "target": spec["id"],
                "track": spec["track"],
                "family": spec["family"],
                "learner_index": index,
                "method": method,
                "training_folder": str(training.relative_to(out)),
                "reference_folder": str(reference_folder.relative_to(out)),
                "training": receipt,
                "points": points,
                "first_qualifying_ceiling": next(
                    (p["ceiling"] for p in points if p["criterion_reached"]), None
                ),
            }
            write(result_path, result)
            write(cell / "result-integrity.json", {"sha256": sha(result_path)})
            all_results.append(result)
        write(
            out / "progress.json",
            {
                "completed_cells": len(all_results),
                "last_target": spec["id"],
                "wall_seconds_this_invocation": time.perf_counter() - started,
            },
        )
    write(out / "results.json", all_results)
    summary = summarize(all_results)
    write(out / "summary.json", summary)
    return summary


def summarize(results):
    groups = {}
    for result in results:
        for point in result["points"]:
            key = (result["track"], result["family"], result["method"], point["ceiling"])
            groups.setdefault(key, {}).setdefault(result["target"], []).append(
                point["metrics"]["overall"]
            )
    summaries = []
    for key, targets in sorted(groups.items()):
        fields = (
            "trace_fidelity",
            "output_fidelity",
            "prediction_coverage",
            "conditional_accuracy",
            "false_supported_rate",
            "abstention_rate",
        )
        values = {}
        for field in fields:
            means = [
                statistics.mean(v[field] for v in samples if v[field] is not None)
                for samples in targets.values()
                if any(v[field] is not None for v in samples)
            ]
            values[field] = {
                "median_target_mean": statistics.median(means) if means else None,
                "range": [min(means), max(means)] if means else None,
            }
        summaries.append(
            {
                "track": key[0],
                "family": key[1],
                "method": key[2],
                "ceiling": key[3],
                "distinct_targets": len(targets),
                "metrics": values,
            }
        )
    paired = []
    for (track, family, method, ceiling), targets in sorted(groups.items()):
        if method not in {"aalpy-state-prefix", "hardened"} or track == "C":
            continue
        baselines = ["aalpy-random-w", "random"] if track == "A" else ["fixed-grid", "adaptive"]
        for baseline in baselines:
            other = groups.get((track, family, baseline, ceiling), {})
            for field in ("trace_fidelity", "prediction_coverage"):
                differences = [
                    statistics.mean(v[field] for v in targets[t])
                    - statistics.mean(v[field] for v in other[t])
                    for t in targets.keys() & other.keys()
                ]
                if differences:
                    paired.append(
                        {
                            "track": track,
                            "family": family,
                            "ceiling": ceiling,
                            "method": method,
                            "baseline": baseline,
                            "metric": field,
                            "target_count": len(differences),
                            "median_difference": statistics.median(differences),
                            "range": [min(differences), max(differences)],
                            "wins_ties_losses": [
                                sum(d > 1e-12 for d in differences),
                                sum(abs(d) <= 1e-12 for d in differences),
                                sum(d < -1e-12 for d in differences),
                            ],
                        }
                    )
    return {
        "cells": len(results),
        "points": sum(len(r["points"]) for r in results),
        "training_actions": sum(r["training"]["costs"]["actions"] for r in results),
        "training_resets": sum(r["training"]["costs"]["resets"] for r in results),
        "status_counts": {
            s: sum(r["training"]["status"] == s for r in results)
            for s in sorted({r["training"]["status"] for r in results})
        },
        "unreached_cells": sum(r["first_qualifying_ceiling"] is None for r in results),
        "groups": summaries,
        "paired_target_differences": paired,
    }
