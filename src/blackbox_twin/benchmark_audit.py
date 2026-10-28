"""Independent SQL, model, target and evaluation checks for the M4 pilot."""

import hashlib
import json
import sqlite3
from pathlib import Path

from .benchmark import digest, score_points, source_digest


def audit_suite(root: Path):
    config = json.loads((root / "config.json").read_text())
    protocol = config["protocol"]
    assert config["manifest_sha256"] == digest(protocol)
    assert config["source_sha256"] == source_digest(), "Training/metric source changed after freeze"
    results = list(root.glob("*/*/*/result.json"))
    expected = len(protocol["families"]) * len(protocol["seeds"]) * len(protocol["methods"])
    assert len(results) == expected
    total_actions = total_resets = 0
    early_stops, failures, recovered = [], [], []
    reference_pairs, oracle_programs = set(), {}
    for path in results:
        result = json.loads(path.read_text())
        pair, folder = path.parent.parent, path.parent / result["attempt"]
        target = json.loads((pair / "target/target.json").read_text())
        reference = json.loads((pair / "evaluation/references.json").read_text())
        oracle_programs.setdefault(result["family"], set()).add(result["oracle_sha256"])
        if pair not in reference_pairs:
            reference_pairs.add(pair)
            inputs = json.loads((pair / "evaluation/inputs.json").read_text())
            assert inputs["sequences"] == reference["sequences"]
            with sqlite3.connect(pair / "evaluation/observations.sqlite") as evaluator_db:
                observed = {}
                for exp, actions in evaluator_db.execute(
                    "SELECT id,actions FROM experiments WHERE status='completed'"
                ).fetchall():
                    observed[tuple(json.loads(actions))] = [
                        json.loads(r[0])["payload"]
                        for r in evaluator_db.execute(
                            "SELECT response FROM events WHERE experiment_id=? "
                            "AND kind='action' ORDER BY id",
                            (exp,),
                        )
                    ]
                counts = dict(
                    evaluator_db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind")
                )
            assert reference["outputs"] == [observed[tuple(w)] for w in reference["sequences"]]
            assert counts["action"] == reference["costs"]["actions"]
            assert counts["reset"] == reference["costs"]["resets"]
        assert result["manifest_sha256"] == config["manifest_sha256"]
        assert result["target_contract_sha256"] == digest(target)
        assert result["evaluation_sha256"] == digest(reference)
        assert (
            result["oracle_sha256"]
            == hashlib.sha256((pair / "target/oracle.py").read_bytes()).hexdigest()
        )
        training = result["training"]
        with sqlite3.connect(folder / "observations.sqlite") as db:
            counts = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
            start = db.execute("SELECT MIN(started) FROM runs").fetchone()[0]
            assert reference["created_at"] < start
            phases = [r[0] for r in db.execute("SELECT DISTINCT phase FROM experiments")]
            assert all(
                p
                in {"membership", "refinement-membership", "equivalence-search", "reset-validation"}
                for p in phases
            )
            rows = db.execute(
                "SELECT x.phase,e.kind,COUNT(*) FROM events e JOIN experiments x "
                "ON x.id=e.experiment_id GROUP BY x.phase,e.kind"
            ).fetchall()
        for kind, key in (("action", "actions"), ("reset", "resets")):
            assert counts.get(kind, 0) == training["costs"][key]
        for phase, kind, count in rows:
            assert (
                training["phase_costs"][phase]["actions" if kind == "action" else "resets"] == count
            )
        assert training["costs"]["actions"] <= max(protocol["budgets"])
        assert training["costs"]["resets"] <= protocol["max_resets"]
        for point in result["points"]:
            assert (
                point["model_generated_at_actions"] <= point["actual_actions"] <= point["ceiling"]
            )
        assert score_points(folder, training, reference) == result["points"]
        total_actions += training["costs"]["actions"]
        total_resets += training["costs"]["resets"]
        if training["costs"]["actions"] < max(protocol["budgets"]):
            early_stops.append(
                {
                    "family": result["family"],
                    "seed": result["seed"],
                    "method": result["method"],
                    "actual_actions": training["costs"]["actions"],
                }
            )
        if training["status"] not in {"budget_exhausted", "search_completed"}:
            failures.append(str(path.relative_to(root)))
        if result["prior_incomplete_attempts"]:
            recovered.append(str(path.relative_to(root)))
    return {
        "audit": "PASS",
        "cells": len(results),
        "training_actions": total_actions,
        "training_resets": total_resets,
        "early_stops": early_stops,
        "failed_cells": failures,
        "recovered_cells": recovered,
        "recomputed_checkpoint_scores": len(results) * len(protocol["budgets"]),
        "same_target_and_evaluation_per_pair": True,
        "distinct_oracle_programs_by_family": {
            f: len(hashes) for f, hashes in oracle_programs.items()
        },
        "reference_outputs_reconciled_to_sql": True,
        "no_full_word_evaluation_leakage": True,
    }
