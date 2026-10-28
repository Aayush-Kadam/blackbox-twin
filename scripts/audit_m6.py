"""Independent M6 source, physical-event, support, metric and evaluation-separation audit."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from blackbox_twin.contracts import Action
from blackbox_twin.m6_run import cells_for, finite_product, model_predictions, summarize, verify
from blackbox_twin.support import SupportedModel, compile_support
from blackbox_twin.typed import action_key


def read(path):
    return json.loads(path.read_text())


def counts(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        values = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
    return {"actions": values.get("action", 0), "resets": values.get("reset", 0)}


def traces(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        return [
            [
                json.loads(value)["payload"]
                for (value,) in db.execute(
                    "SELECT response FROM events WHERE experiment_id=? "
                    "AND kind='action' ORDER BY id",
                    (exp,),
                )
            ]
            for (exp,) in db.execute("SELECT id FROM experiments ORDER BY rowid").fetchall()
        ]


def audit(project, root):
    protocol = read(root / "protocol.json")
    results = read(root / "results.json")
    assert read(root / "summary.json") == summarize(results)
    expected = sum(len(cells_for(spec, protocol)) for spec in protocol["targets"])
    assert len(results) == expected
    for name, digest in protocol["source_sha256"].items():
        assert (
            hashlib.sha256((root / "source-snapshot/blackbox_twin" / name).read_bytes()).hexdigest()
            == digest
        )
    for name, digest in protocol.get("resources_sha256", {}).items():
        assert hashlib.sha256((project / name).read_bytes()).hexdigest() == digest
    last_prepare = max(
        read(root / spec["id"] / "prepared.json")["frozen_at"] for spec in protocol["targets"]
    )
    reference_actions = reference_resets = training_actions = training_resets = 0
    evaluated_points, support_models = 0, 0
    overlaps, failures, early_stops = [], [], []
    for spec in protocol["targets"]:
        target = root / spec["id"]
        verify(target / "target")
        prepared = read(target / "prepared.json")
        assert (
            hashlib.sha256((target / "target/oracle.py").read_bytes()).hexdigest()
            == prepared["target_sha256"]
        )
        assert (
            hashlib.sha256((target / "target/inputs.json").read_bytes()).hexdigest()
            == prepared["inputs_sha256"]
        )
        if spec["track"] == "A" and spec["family"] == "rare" and spec["variant"] == 0:
            assert (target / "target/oracle.py").read_bytes() == (
                project / "evidence/m4-1/target-rare-access/oracle.py"
            ).read_bytes()
        cases = read(target / "target/inputs.json")
        reference_paths = {r["reference_folder"] for r in results if r["target"] == spec["id"]}
        assert len(reference_paths) == 1
        reference = root / next(iter(reference_paths))
        verify(reference)
        truth = read(reference / "receipt.json")
        assert truth["outputs"] == traces(reference / "observations.sqlite")
        counted = counts(reference / "observations.sqlite")
        assert counted == {k: truth["costs"][k] for k in counted}
        reference_actions += counted["actions"]
        reference_resets += counted["resets"]
        for result in [r for r in results if r["target"] == spec["id"]]:
            folder = root / result["training_folder"]
            verify(folder)
            receipt = read(folder / "receipt.json")
            assert receipt == result["training"]
            physical = counts(folder / "observations.sqlite")
            assert physical == {k: receipt["costs"][k] for k in physical}
            assert sum(p["actions"] for p in receipt["phase_costs"].values()) == physical["actions"]
            training_actions += physical["actions"]
            training_resets += physical["resets"]
            with sqlite3.connect(
                f"file:{(folder / 'observations.sqlite').as_posix()}?mode=ro", uri=True
            ) as db:
                assert (
                    last_prepare
                    < db.execute("SELECT started FROM runs ORDER BY rowid LIMIT 1").fetchone()[0]
                )
                training_words = {
                    tuple(json.loads(v)) for (v,) in db.execute("SELECT actions FROM experiments")
                }
                if spec["track"] == "B":
                    amounts = {
                        json.loads(v)["arguments"].get("amount")
                        for (v,) in db.execute("SELECT request FROM events WHERE kind='action'")
                    }
                    assert not amounts & set(protocol["reserved_values"])
            if receipt["status"].startswith(("failed", "model_class_failure")):
                failures.append(
                    {"target": spec["id"], "method": result["method"], "status": receipt["status"]}
                )
            if physical["actions"] < max(p["ceiling"] for p in result["points"]):
                early_stops.append(
                    {
                        "target": spec["id"],
                        "method": result["method"],
                        "spent": physical["actions"],
                        "status": receipt["status"],
                    }
                )
            for point in result["points"]:
                assert point["actual_actions"] <= point["ceiling"]
                model = read(folder / point["model"])
                if model["schema_version"] == 3:
                    parsed = SupportedModel.model_validate(model)
                    assert (
                        compile_support(
                            parsed.contract,
                            parsed.observations,
                            parsed.provenance["refinement_history"],
                        )
                        == parsed
                    )
                    support_models += 1
                evaluation = root / point["evaluation_folder"]
                verify(evaluation)
                actual = read(evaluation / "receipt.json")["outputs"]
                assert actual == traces(evaluation / "observations.sqlite")
                groups = {}
                for case, expected_trace, actual_trace in zip(
                    cases, truth["outputs"], actual, strict=True
                ):
                    assert model_predictions(model, case["actions"])[0] == actual_trace
                    group = groups.setdefault(case["category"], [0, 0, 0, 0, 0, 0])
                    group[0] += 1
                    group[1] += expected_trace == actual_trace
                    group[2] += len(actual_trace)
                    group[3] += sum(
                        a == b for a, b in zip(actual_trace, expected_trace, strict=True)
                    )
                    group[4] += sum(not a.get("bbt_unsupported") for a in actual_trace)
                    group[5] += sum(
                        not a.get("bbt_unsupported") and a == b
                        for a, b in zip(actual_trace, expected_trace, strict=True)
                    )
                    if spec["track"] == "B":
                        frozen_word = tuple(
                            action_key(Action.model_validate(a)) for a in case["actions"]
                        )
                    else:
                        inner = model.get("finite") if model["schema_version"] == 4 else model
                        symbols = {
                            json.dumps(a, sort_keys=True): k
                            for k, a in (inner or {}).get("actions", {}).items()
                        }
                        frozen_word = tuple(
                            symbols.get(json.dumps(a, sort_keys=True), "<unknown>")
                            for a in case["actions"]
                        )
                    if frozen_word in training_words:
                        overlaps.append(
                            {
                                "target": spec["id"],
                                "method": result["method"],
                                "category": case["category"],
                            }
                        )
                for category, (
                    n,
                    exact,
                    steps,
                    output_matches,
                    concrete,
                    correct,
                ) in groups.items():
                    measured = point["metrics"]["groups"][category]
                    assert (n, exact, steps, output_matches, concrete, correct) == (
                        measured["traces"],
                        measured["exact_traces"],
                        measured["outputs"],
                        measured["exact_outputs"],
                        measured["concrete_outputs"],
                        measured["correct_concrete_outputs"],
                    )
                    assert measured["prediction_coverage"] == concrete / steps
                    assert measured["conditional_accuracy"] == (
                        correct / concrete if concrete else None
                    )
                    assert measured["false_supported_rate"] == (
                        (concrete - correct) / concrete if concrete else None
                    )
                    assert measured["abstention_rate"] == (steps - concrete) / steps
                if spec["track"] == "A":
                    assert point["finite_product"] == finite_product(
                        read(target / "target/evaluator-table.json"), model
                    )
                overall = point["metrics"]["overall"]
                criterion = (
                    overall["trace_fidelity"] >= 0.95 and overall["prediction_coverage"] >= 0.95
                )
                assert point["criterion_reached"] == (
                    criterion and receipt["status"] in {"completed", "action_budget"}
                )
                evaluated_points += 1
    original_training_dbs = list(root.glob("*/seed-*/training/attempt-*/observations.sqlite"))
    reference_dbs = list(root.glob("*/reference/attempt-*/observations.sqlite"))
    all_actions = sum(counts(p)["actions"] for p in original_training_dbs)
    all_reference = sum(counts(p)["actions"] for p in reference_dbs)
    twin_dbs = list(root.glob("*/seed-*/evaluation-*/attempt-*/observations.sqlite"))
    twin_dbs += list(root.glob("*/seed-*/training/attempt-*/twin-observations.sqlite"))
    return {
        "audit": "PASS",
        "cells": len(results),
        "scored_points": evaluated_points,
        "training_actions_completed_attempts": training_actions,
        "training_resets_completed_attempts": training_resets,
        "all_attempt_training_actions": all_actions,
        "partial_attempt_training_actions": all_actions - training_actions,
        "reference_actions": reference_actions,
        "reference_resets": reference_resets,
        "partial_reference_actions": all_reference - reference_actions,
        "twin_actions": sum(counts(p)["actions"] for p in twin_dbs),
        "twin_resets": sum(counts(p)["resets"] for p in twin_dbs),
        "support_models_recompiled": support_models,
        "failures": failures,
        "early_stops": early_stops,
        "full_word_overlap_cases": overlaps,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.project, args.out), indent=2))
