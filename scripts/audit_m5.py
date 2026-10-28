"""Read-only physical-count, model-fit, evaluation-score and isolation audit for M5."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from blackbox_twin.contracts import Action
from blackbox_twin.guards import GuardedModel
from blackbox_twin.typed import action_key
from blackbox_twin.typed_runtime import guarded_step


def read(path):
    return json.loads(path.read_text())


def counts(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        result = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
    return {"actions": result.get("action", 0), "resets": result.get("reset", 0)}


def traces(path):
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        return [
            [
                json.loads(r[0])["payload"]
                for r in db.execute(
                    "SELECT response FROM events WHERE experiment_id=? AND kind='action' "
                    "ORDER BY id",
                    (exp,),
                )
            ]
            for (exp,) in db.execute("SELECT id FROM experiments ORDER BY rowid").fetchall()
        ]


def audit(project, suite):
    protocol = read(suite / "protocol.json")
    contract = protocol["contract"]
    for name, digest in protocol["freeze"]["files"].items():
        assert hashlib.sha256((project / name).read_bytes()).hexdigest() == digest
    for name, digest in protocol["source_sha256"].items():
        path = suite / "source-snapshot/blackbox_twin" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    result = {
        "audit": "PASS",
        "training_actions": 0,
        "training_resets": 0,
        "reference_actions": 0,
        "reference_resets": 0,
        "cells": [],
    }
    for variant, pair in read(suite / "summary.json").items():
        folder = suite / variant
        fingerprint = read(folder / "target-fingerprint.json")
        assert (
            hashlib.sha256((folder / "oracle.py").read_bytes()).hexdigest() == fingerprint["sha256"]
        )
        cases = read(folder / "evaluation-cases.json")
        assert cases[: len(read(suite / "frozen-inputs.json"))] == read(
            suite / "frozen-inputs.json"
        )
        truth = read(folder / "evaluation-reference/references.json")
        assert truth["outputs"] == traces(folder / "evaluation-reference/observations.sqlite")
        reference = counts(folder / "evaluation-reference/observations.sqlite")
        assert reference == {k: truth["costs"][k] for k in reference}
        result["reference_actions"] += reference["actions"]
        result["reference_resets"] += reference["resets"]
        for method, training in pair["training"].items():
            cell = folder / method
            assert read(cell / "training.json") == training
            physical = counts(cell / "observations.sqlite")
            assert physical == {k: training["costs"][k] for k in physical}
            assert physical["actions"] <= contract["training_budget"]["max_actions"]
            assert physical["resets"] <= contract["training_budget"]["max_resets"]
            assert (
                sum(v["actions"] for v in training["phase_costs"].values()) == physical["actions"]
            )
            with sqlite3.connect(cell / "observations.sqlite") as db:
                values = set()
                for (request,) in db.execute("SELECT request FROM events WHERE kind='action'"):
                    arguments = json.loads(request)["arguments"]
                    if type(arguments.get("amount")) is int:
                        values.add(arguments["amount"])
                assert not values & set(contract["reserved_evaluation_values"])
                words = {
                    tuple(json.loads(w)) for (w,) in db.execute("SELECT actions FROM experiments")
                }
                started = db.execute("SELECT started FROM runs").fetchone()[0]
                assert protocol["frozen_at"] < started
            frozen_words = {
                tuple(action_key(Action.model_validate(a)) for a in c["actions"])
                for c in read(suite / "frozen-inputs.json")
            }
            assert not frozen_words & words, "Held-out full sequence overlaps physical training"
            model = GuardedModel.model_validate_json((cell / training["model"]).read_text())
            encoded = model.model_dump()
            for row in model.observations:
                _, output = guarded_step(encoded, (row["balance"], row["frozen"]), row["action"])
                assert output == row["output"]
            evaluator = folder / ("evaluation-" + method)
            measured = traces(evaluator / "observations.sqlite")
            assert measured == read(evaluator / "references.json")["outputs"]
            groups = {}
            points = []
            for case, expected, actual in zip(cases, truth["outputs"], measured, strict=True):
                state, predicted = (0, False), []
                for action in case["actions"]:
                    state, output = guarded_step(encoded, state, action)
                    predicted.append(output)
                assert predicted == actual, (
                    "Serialized model and independently executed twin differ"
                )
                group = groups.setdefault(case["category"], [0, 0, 0, 0, 0])
                group[0] += 1
                group[1] += actual == expected
                group[2] += len(expected)
                group[3] += sum(a == b for a, b in zip(expected, actual, strict=True))
                group[4] += sum(o.get("bbt_unsupported") is True for o in actual)
                if case["category"] == "exhaustive":
                    index = case["probe_index"]
                    points.append((case, expected[index], actual[index]))
            for category, (n, exact, steps, matches, unsupported) in groups.items():
                saved = pair["evaluation"][method]["groups"][category]
                assert (n, exact, steps, matches, unsupported) == (
                    saved["traces"],
                    saved["trace_matches"],
                    saved["outputs"],
                    saved["output_matches"],
                    saved["unsupported"],
                )
                assert saved["trace_fidelity"] == exact / n
                assert saved["output_fidelity"] == matches / steps
            expected_accept = sum(a.get("status") == "ok" for _, a, _ in points)
            predicted_accept = sum(b.get("status") == "ok" for _, _, b in points)
            correct_accept = sum(a.get("status") == b.get("status") == "ok" for _, a, b in points)
            saved_evaluation = pair["evaluation"][method]
            assert saved_evaluation["guard_population"] == len(points)
            assert saved_evaluation["guard_precision"] == correct_accept / predicted_accept
            assert saved_evaluation["guard_recall"] == correct_accept / expected_accept
            boundary_sets = [set(), set()]
            for (left, a, b), (right, c, d) in zip(points, points[1:], strict=False):
                if left["context"] != right["context"] or left["operation"] != right["operation"]:
                    continue
                for index, before, after in [(0, a, c), (1, b, d)]:
                    key_before = before.get(
                        "error", "ok" if before.get("status") == "ok" else "unsupported"
                    )
                    key_after = after.get(
                        "error", "ok" if after.get("status") == "ok" else "unsupported"
                    )
                    if key_before != key_after:
                        boundary_sets[index].add(
                            (*left["context"], left["operation"], left["value"])
                        )
            assert saved_evaluation["boundaries"] == {
                "target": len(boundary_sets[0]),
                "twin": len(boundary_sets[1]),
                "matched": len(boundary_sets[0] & boundary_sets[1]),
                "exact": boundary_sets[0] == boundary_sets[1],
            }
            if method == "adaptive":
                initial = read(cell / "revision-000/model.json")
                baseline = read(folder / "fixed-grid/revision-000/model.json")
                assert initial["rules"] == baseline["rules"]
                assert initial["states"] == baseline["states"]
                assert training["counterexamples"]
                assert all(c["status"] == "agreement" for c in training["counterexample_replays"])
                assert training["regressions"]["passed"] == training["regressions"]["tested"]
            result["training_actions"] += physical["actions"]
            result["training_resets"] += physical["resets"]
            result["cells"].append(
                {
                    "variant": variant,
                    "method": method,
                    "values_used": sorted(values),
                    "physical_costs": physical,
                    "scores_recomputed": len(cases),
                }
            )
    twin_dbs = list(suite.glob("*/adaptive/twin-observations.sqlite"))
    twin_dbs += list(suite.glob("*/evaluation-fixed-grid/observations.sqlite"))
    twin_dbs += list(suite.glob("*/evaluation-adaptive/observations.sqlite"))
    result["separate_twin_actions"] = sum(counts(p)["actions"] for p in twin_dbs)
    result["separate_twin_resets"] = sum(counts(p)["resets"] for p in twin_dbs)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.project, args.suite), indent=2))
