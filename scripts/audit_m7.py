"""Read-only reconciliation of a completed M7 demonstration and preserved M6 evidence."""

import argparse
import json
import sqlite3
from pathlib import Path

from blackbox_twin.contracts import BehavioralModel, Observation
from blackbox_twin.differential import compare_traces
from blackbox_twin.m7_data import db_counts, read, sha


def preserved_m6(project):
    from blackbox_twin.m6_run import summarize, verify

    root = project / "evidence/m6-confirmatory-v1"
    results = read(root / "results.json")
    assert read(root / "summary.json") == summarize(results)
    verified = 0
    for path in root.rglob("integrity.json"):
        verify(path.parent)
        verified += 1
    for result in results:
        cell = (root / result["training_folder"]).parent.parent
        assert read(cell / "result.json") == result
        assert sha(cell / "result.json") == read(cell / "result-integrity.json")["sha256"]
    protocol = read(root / "protocol.json")
    current_changes = []
    for name, digest in protocol["source_sha256"].items():
        assert sha(root / "source-snapshot/blackbox_twin" / name) == digest
        if sha(project / "src/blackbox_twin" / name) != digest:
            current_changes.append(name)
    return {
        "verification": "PASS",
        "artifact_folders_verified": verified,
        "cells_reconciled": len(results),
        "scored_points": sum(len(r["points"]) for r in results),
        "all_frozen_engine_source_hashes_match": True,
        "current_engine_changes_since_m6": current_changes,
        "training_actions": sum(r["training"]["costs"]["actions"] for r in results),
        "scope": "Read-only integrity reconciliation; no oracle queries or new benchmark.",
    }


def traces(path, phase):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        result = {}
        for experiment, word in db.execute(
            "SELECT id,actions FROM experiments WHERE phase=? ORDER BY rowid", (phase,)
        ).fetchall():
            result[tuple(json.loads(word))] = [
                json.loads(v)["payload"]
                for (v,) in db.execute(
                    "SELECT response FROM events WHERE experiment_id=? "
                    "AND kind='action' ORDER BY id",
                    (experiment,),
                )
            ]
    return result


def inspect(root, saved):
    database = root / "observations.sqlite"
    for twin in (False, True):
        actual = db_counts(database, twin)
        assert actual == {k: saved["twin_costs" if twin else "original_costs"][k] for k in actual}
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        phases = db.execute(
            "SELECT x.phase,e.kind,COUNT(*) FROM events e JOIN experiments x "
            "ON x.id=e.experiment_id GROUP BY x.phase,e.kind"
        ).fetchall()
        words = {
            tuple(json.loads(v))
            for (v,) in db.execute("SELECT actions FROM experiments WHERE phase NOT LIKE 'twin:%'")
        }
        first_start = db.execute("SELECT MIN(started) FROM runs").fetchone()[0]
    for phase, kind, count in phases:
        assert saved["phase_costs"][phase]["actions" if kind == "action" else "resets"] == count
    return words, first_start


def audit(project, folder):
    loop, evaluation = (
        read(folder / "loop/summary.json"),
        read(folder / "evaluation/evaluation.json"),
    )
    receipt = read(folder / "receipt.json")
    assert receipt["status"] == "completed"
    words, first_start = inspect(folder / "loop", loop)
    inspect(folder / "evaluation", evaluation)
    frozen = read(folder / "heldout-sequences.json")
    assert frozen == read(folder / "evaluation/frozen-sequences.json")
    assert frozen["created_at"] < first_start
    assert not words.intersection(map(tuple, frozen["sequences"]))
    models = []
    for revision in loop["revisions"]:
        path = folder / "loop" / revision["model"]
        assert sha(path) == revision["model_file_sha256"]
        assert sha(folder / "loop" / revision["twin"]) == revision["twin_file_sha256"]
        models.append(BehavioralModel.model_validate(read(path)))
    for label in ("initial", "refined"):
        original = traces(folder / "evaluation/observations.sqlite", "held-out/" + label)
        twin = traces(folder / "evaluation/observations.sqlite", "twin:held-out/" + label)
        assert set(original) == set(twin) == set(map(tuple, frozen["sequences"]))
        expected = evaluation["scores"][label]
        assert expected["traces"] == len(original)
        assert expected["trace_matches"] == sum(original[w] == twin[w] for w in original)
        assert expected["steps"] == sum(len(v) for v in original.values())
        assert expected["step_matches"] == sum(
            a == b for w in original for a, b in zip(original[w], twin[w], strict=True)
        )
        assert expected["trace_match_rate"] == expected["trace_matches"] / expected["traces"]
        assert expected["step_match_rate"] == expected["step_matches"] / expected["steps"]
    discovery = read(next((folder / "loop/counterexamples").glob("*/discovery.json")))
    for label in ("original", "minimized"):
        case = discovery["minimization"][label]
        comparison = compare_traces(
            case["actions"],
            [Observation.model_validate(o) for o in case["original"]],
            [Observation.model_validate(o) for o in case["twin"]],
        )
        assert comparison.is_mismatch and comparison.first_divergence == case["first_divergence"]
        assert comparison.raw_original == case["raw_original"]
        assert comparison.raw_twin == case["raw_twin"]
    minimized = discovery["minimization"]["minimized"]
    assert [o.payload for o in models[0].predict(minimized["actions"])] != minimized["raw_original"]
    assert [o.payload for o in models[-1].predict(minimized["actions"])] == minimized[
        "raw_original"
    ]
    assert discovery["minimization"]["locally_minimal"]
    for iteration in loop["iterations"]:
        if "regressions" in iteration:
            assert iteration["regressions"]["checked"] == iteration["regressions"]["passed"]
            assert iteration["regressions"]["new_regressions"] == 0
    assert receipt["scores"] == evaluation["scores"]
    assert not receipt["equivalence_proven"] and not evaluation["equivalence_proven"]
    config = read(folder / "config.json")
    source_frozen = "package_source_sha256" in config
    historical_source_changes = []
    if source_frozen:
        assert config["frozen_inputs_sha256"] == sha(folder / "heldout-sequences.json")
        assert config["fixture_sha256"] == sha(project / "fixtures/targets/delayed_process.py")
        assert config["target_manifest_sha256"] == sha(project / "examples/delayed/target.json")
        for name, digest in config["package_source_sha256"].items():
            if sha(project / "src/blackbox_twin" / name) != digest:
                assert (
                    sha(project / "evidence/m8-baseline/source-snapshot/blackbox_twin" / name)
                    == digest
                )
                historical_source_changes.append(name)
    old_protocol = read(project / "evidence/m6-confirmatory-v1/protocol.json")
    for name, digest in old_protocol["source_sha256"].items():
        assert (
            sha(project / "evidence/m6-confirmatory-v1/source-snapshot/blackbox_twin" / name)
            == digest
        )
    for name, digest in old_protocol["resources_sha256"].items():
        assert sha(project / name) == digest
    return {
        "audit": "PASS",
        "folder": str(folder),
        "source_frozen": source_frozen,
        "training": loop["original_costs"],
        "evaluation": evaluation["original_costs"],
        "twin_training": loop["twin_costs"],
        "twin_evaluation": evaluation["twin_costs"],
        "isolated_requests": receipt["isolated_twin_requests"],
        "states": [len(m.transitions) for m in models],
        "scores": evaluation["scores"],
        "wall_seconds": receipt["wall_seconds"],
        "full_word_overlap": 0,
        "first_divergence_zero_based": minimized["first_divergence"],
        "minimized_actions": minimized["actions"],
        "m6_frozen_engine_sources_preserved": True,
        "historical_source_changes": historical_source_changes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--m6-only", action="store_true")
    args = parser.parse_args()
    if args.m6_only:
        result = preserved_m6(args.project.resolve())
    elif args.run:
        result = audit(args.project.resolve(), args.run.resolve())
    else:
        parser.error("Specify --run or --m6-only")
    print(json.dumps(result, indent=2))
