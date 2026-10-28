"""Independently verify persisted M3 phase counts, identities and held-out separation."""

import hashlib
import json
import sqlite3
from pathlib import Path

from blackbox_twin.contracts import BehavioralModel
from blackbox_twin.counterexamples import Corpus, model_id

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "evidence/m3-demo"


def inspect(folder, summary):
    with sqlite3.connect(folder / "observations.sqlite") as db:
        rows = db.execute(
            "SELECT x.phase,e.kind,COUNT(*) FROM events e JOIN experiments x "
            "ON x.id=e.experiment_id GROUP BY x.phase,e.kind"
        ).fetchall()
        words = {
            tuple(json.loads(row[0]))
            for row in db.execute("SELECT actions FROM experiments WHERE phase NOT LIKE 'twin:%'")
        }
        comparisons = [
            json.loads(row[0])
            for row in db.execute("SELECT content FROM artifacts WHERE kind='comparison'")
        ]
    for side in ("original", "twin"):
        for kind, key in (("action", "actions"), ("reset", "resets")):
            total = sum(
                count
                for phase, event, count in rows
                if event == kind and phase.startswith("twin:") == (side == "twin")
            )
            assert total == summary[f"{side}_costs"][key], (side, key, total)
    for phase, kind, total in rows:
        assert summary["phase_costs"][phase]["actions" if kind == "action" else "resets"] == total
    return words, comparisons


def main():
    loop = json.loads((DEMO / "loop/summary.json").read_text())
    evaluation = json.loads((DEMO / "evaluation/evaluation.json").read_text())
    training_words, comparisons = inspect(DEMO / "loop", loop)
    inspect(DEMO / "evaluation", evaluation)
    frozen = json.loads((DEMO / "heldout-sequences.json").read_text())
    copied = json.loads((DEMO / "evaluation/frozen-sequences.json").read_text())
    assert frozen == copied
    assert len(frozen["sequences"]) == len(set(map(tuple, frozen["sequences"]))) == 100
    assert not training_words.intersection(map(tuple, frozen["sequences"]))
    models = []
    for revision in loop["revisions"]:
        model_file = DEMO / "loop" / revision["model"]
        twin_file = DEMO / "loop" / revision["twin"]
        model = BehavioralModel.model_validate_json(model_file.read_text())
        assert revision["model_id"] == model_id(model)
        assert revision["model_file_sha256"] == hashlib.sha256(model_file.read_bytes()).hexdigest()
        assert revision["twin_file_sha256"] == hashlib.sha256(twin_file.read_bytes()).hexdigest()
        models.append(model)
    assert [len(model.transitions) for model in models] == [1, 5]
    assert loop["resolved_counterexamples"] == 1
    record = Corpus.read(next((DEMO / "loop/counterexamples").glob("*/discovery.json")))
    original, minimized = record.minimization.original, record.minimization.minimized
    assert original.is_mismatch and minimized.is_mismatch
    assert record.minimization.locally_minimal
    assert models[0].predict(minimized.actions) != minimized.original
    assert models[1].predict(minimized.actions) == minimized.original
    for word in (original.actions, minimized.actions):
        assert any(
            result["actions"] == word and result["status"] == "agreement" for result in comparisons
        )
    assert loop["iterations"][0]["regressions"]["new_regressions"] == 0
    with sqlite3.connect(DEMO / "loop/observations.sqlite") as db:
        first_start = db.execute("SELECT MIN(started) FROM runs").fetchone()[0]
        fed = [
            json.loads(row[0])
            for row in db.execute(
                "SELECT content FROM artifacts WHERE kind='confirmed_counterexample_returned'"
            )
        ]
    assert frozen["created_at"] < first_start
    assert fed and fed[0]["expected"][-1] != fed[0]["hypothesis_outputs"][-1]
    totals = {
        key: loop["original_costs"][key] + evaluation["original_costs"][key]
        for key in ("actions", "resets")
    }
    result = {
        "audit": "PASS",
        "original_totals_including_paired_evaluation": totals,
        "loop_original_costs": loop["original_costs"],
        "paired_evaluation_original_costs": evaluation["original_costs"],
        "scores": evaluation["scores"],
        "training_holdout_full_word_overlap": 0,
        "frozen_before_initial_learning": True,
        "resolved_counterexamples": 1,
    }
    clean = ROOT / "evidence/m3-clean-reproduction"
    if (clean / "evaluation/evaluation.json").exists():
        repeated_loop = json.loads((clean / "loop/summary.json").read_text())
        repeated_evaluation = json.loads((clean / "evaluation/evaluation.json").read_text())
        inspect(clean / "loop", repeated_loop)
        inspect(clean / "evaluation", repeated_evaluation)
        assert repeated_evaluation["scores"] == evaluation["scores"]
        for side in ("original", "twin"):
            for key in ("actions", "resets"):
                assert repeated_loop[f"{side}_costs"][key] == loop[f"{side}_costs"][key]
                assert repeated_evaluation[f"{side}_costs"][key] == evaluation[f"{side}_costs"][key]
        for index, model in enumerate(models):
            repeated = BehavioralModel.model_validate_json(
                (clean / "loop" / repeated_loop["revisions"][index]["model"]).read_text()
            )
            assert repeated.model_dump(exclude={"provenance"}) == model.model_dump(
                exclude={"provenance"}
            )
        result["clean_noneditable_reproduction"] = {
            "audit": "PASS",
            "same_behavioral_tables": True,
            "same_physical_counts": True,
            "same_paired_scores": True,
            "loop_wall_seconds": repeated_loop["wall_seconds"],
            "evaluation_wall_seconds": repeated_evaluation["wall_seconds"],
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
