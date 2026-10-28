"""Reconcile frozen source, support compilation, physical costs, leakage and coverage metrics."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from blackbox_twin.contracts import Action
from blackbox_twin.m51 import predict_trace
from blackbox_twin.support import SupportedModel, compile_support
from blackbox_twin.typed import action_key


def read(path):
    return json.loads(path.read_text())


def counts(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        counts = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
    return {"actions": counts.get("action", 0), "resets": counts.get("reset", 0)}


def traces(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        return [
            [
                json.loads(value)["payload"]
                for (value,) in db.execute(
                    "SELECT response FROM events WHERE experiment_id=? AND kind='action' "
                    "ORDER BY id",
                    (exp,),
                )
            ]
            for (exp,) in db.execute("SELECT id FROM experiments ORDER BY rowid").fetchall()
        ]


def evidence_rows(path):
    result = set()
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        for (exp,) in db.execute("SELECT id FROM experiments ORDER BY rowid").fetchall():
            state = (0, False)
            for request, response, status in db.execute(
                "SELECT request,response,status FROM events WHERE experiment_id=? "
                "AND kind='action' ORDER BY id",
                (exp,),
            ):
                if status != "ok":
                    break
                action, output = json.loads(request), json.loads(response)["payload"]
                result.add(
                    (
                        exp,
                        *state,
                        json.dumps(action, sort_keys=True),
                        json.dumps(output, sort_keys=True),
                    )
                )
                state = output["balance"], output["frozen"]
    return result


def check_metrics(cases, truth, predicted, saved):
    points = []
    for category in {c["category"] for c in cases}:
        rows = [
            (c, a, b)
            for c, a, b in zip(cases, truth, predicted, strict=True)
            if c["category"] == category
        ]
        group = saved["groups"][category]
        n, steps = len(rows), sum(len(a) for _, a, _ in rows)
        exact = sum(a == b for _, a, b in rows)
        concrete = sum(not p.get("bbt_unsupported") for _, _, values in rows for p in values)
        correct = sum(
            not p.get("bbt_unsupported") and p == t
            for _, expected, actual in rows
            for p, t in zip(actual, expected, strict=True)
        )
        all_matches = sum(
            p == t for _, expected, actual in rows for p, t in zip(actual, expected, strict=True)
        )
        full = sum(all(not p.get("bbt_unsupported") for p in actual) for _, _, actual in rows)
        assert group["traces"] == n and group["exact_traces"] == exact
        assert group["outputs"] == steps and group["exact_outputs"] == all_matches
        assert (
            group["concrete_outputs"] == concrete and group["correct_concrete_outputs"] == correct
        )
        assert (
            group["trace_fidelity"] == exact / n and group["output_fidelity"] == all_matches / steps
        )
        assert (
            group["prediction_coverage"] == concrete / steps
            and group["abstention_rate"] == (steps - concrete) / steps
        )
        assert group["conditional_accuracy"] == (correct / concrete if concrete else None)
        assert group["false_supported_rate"] == (
            (concrete - correct) / concrete if concrete else None
        )
        assert group["sequence_coverage"] == full / n
        if category == "exhaustive":
            points = [
                (
                    a[c["probe_index"]].get("status") == "ok",
                    b[c["probe_index"]].get("status") == "ok",
                )
                for c, a, b in rows
            ]
    true_positive = sum(a and b for a, b in points)
    p, t = sum(b for _, b in points), sum(a for a, _ in points)
    assert saved["guard_population"] == len(points)
    assert saved["guard_precision"] == (true_positive / p if p else None)
    assert saved["guard_recall"] == (true_positive / t if t else None)


def audit(project, suite):
    protocol = read(suite / "protocol.json")
    for name, value in protocol["source_sha256"].items():
        assert (
            hashlib.sha256(
                (suite / "source-snapshot/blackbox_twin" / name).read_bytes()
            ).hexdigest()
            == value
        )
    assert (
        hashlib.sha256(
            (project / "fixtures/targets/typed_wallet_process.py").read_bytes()
        ).hexdigest()
        == protocol["fixture_sha256"]
    )
    result = {
        "audit": "PASS",
        "training_actions": 0,
        "training_resets": 0,
        "reference_actions": 0,
        "reference_resets": 0,
        "cells": [],
        "recompiled_support_models": 0,
    }
    for variant, pair in read(suite / "summary.json").items():
        folder = suite / variant
        generation = read(folder / "generation.json")
        assert (
            hashlib.sha256((folder / "oracle.py").read_bytes()).hexdigest() == generation["sha256"]
        )
        cases = read(folder / "evaluation-cases.json")
        frozen = read(suite / "frozen-inputs.json")
        assert cases[: len(frozen)] == frozen
        truth = read(folder / "evaluation-reference/references.json")
        assert truth["outputs"] == traces(folder / "evaluation-reference/observations.sqlite")
        physical = counts(folder / "evaluation-reference/observations.sqlite")
        assert physical == {k: truth["costs"][k] for k in physical}
        result["reference_actions"] += physical["actions"]
        result["reference_resets"] += physical["resets"]
        for method, receipt in pair["training"].items():
            cell = folder / method
            assert receipt == read(cell / "training.json")
            databases = [cell / "observations.sqlite"]
            if method == "hardened":
                databases.append(cell / "legacy-seed/observations.sqlite")
                assert len(receipt["probes"]) <= protocol["max_probes"]
                assert all(
                    p["actual_actions"] == p["estimated_actions"] == len(p["access"]) + 1
                    for p in receipt["probes"]
                )
                assert sum(p["actual_actions"] for p in receipt["probes"]) == receipt[
                    "additional_phase_costs"
                ].get("ambiguity-resolution", {}).get("actions", 0)
            spent = {k: sum(counts(p)[k] for p in databases) for k in ("actions", "resets")}
            assert spent == {k: receipt["costs"][k] for k in spent}
            assert spent["actions"] <= 5000 and spent["resets"] <= 1000
            words, values = set(), set()
            for database in databases:
                with sqlite3.connect(database) as db:
                    assert (
                        protocol["frozen_at"]
                        < db.execute("SELECT started FROM runs ORDER BY rowid LIMIT 1").fetchone()[
                            0
                        ]
                    )
                    words.update(
                        tuple(json.loads(w))
                        for (w,) in db.execute("SELECT actions FROM experiments")
                    )
                    for (request,) in db.execute("SELECT request FROM events WHERE kind='action'"):
                        value = json.loads(request)["arguments"].get("amount")
                        if type(value) is int:
                            values.add(value)
            assert not values & set(protocol["contract"]["reserved_evaluation_values"])
            overlaps = {
                category: sum(
                    tuple(action_key(Action.model_validate(a)) for a in c["actions"]) in words
                    for c in frozen
                    if c["category"] == category
                )
                for category in ("seen", "unseen")
            }
            assert overlaps["unseen"] == 0
            model = read(cell / receipt["model"])
            if method == "hardened":
                parsed = SupportedModel.model_validate(model)
                evidence = set().union(*(evidence_rows(p) for p in databases))
                for row in parsed.observations:
                    assert row["amount"] == row["action"]["arguments"].get("amount", 0)
                    assert (
                        row["experiment"],
                        row["balance"],
                        row["frozen"],
                        json.dumps(row["action"], sort_keys=True),
                        json.dumps(row["output"], sort_keys=True),
                    ) in evidence
                rebuilt = compile_support(
                    parsed.contract, parsed.observations, parsed.provenance["refinement_history"]
                )
                assert parsed == rebuilt
                assert receipt["regressions"]["tested"] == receipt["regressions"]["passed"]
                result["recompiled_support_models"] += 1
            result["training_actions"] += spent["actions"]
            result["training_resets"] += spent["resets"]
            result["cells"].append(
                {
                    "variant": variant,
                    "method": method,
                    "costs": spent,
                    "values_used": sorted(values),
                    "full_word_overlap": overlaps,
                }
            )
        for method, saved in pair["evaluation"].items():
            evaluator = folder / ("evaluation-" + method)
            predicted = traces(evaluator / "observations.sqlite")
            assert predicted == read(evaluator / "references.json")["outputs"]
            model = (
                read(folder / "policy-only.json")
                if method == "policy-only"
                else read(folder / method / pair["training"][method]["model"])
            )
            metadata = []
            for case, actual in zip(cases, predicted, strict=True):
                outputs, statuses = predict_trace(model, case["actions"])
                assert outputs == actual
                metadata.append(statuses)
            assert metadata == read(evaluator / "support.json")
            check_metrics(cases, truth["outputs"], predicted, saved)
            if method in {"hardened", "policy-only"}:
                assert all(g["false_supported_rate"] in (None, 0) for g in saved["groups"].values())
    twin_dbs = list(suite.glob("*/evaluation-*/observations.sqlite"))
    twin_dbs += list(suite.glob("*/adaptive/twin-observations.sqlite"))
    twin_dbs += list(suite.glob("*/hardened/twin-observations.sqlite"))
    result["separate_twin_costs"] = {
        k: sum(counts(p)[k] for p in twin_dbs) for k in ("actions", "resets")
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.project, args.suite), indent=2))
