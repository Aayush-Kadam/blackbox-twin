"""Check the committed demo's counts and full-sequence hold-out separation."""

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
training = ROOT / "evidence/demo-training-v2"
evaluation = ROOT / "evidence/demo-heldout"
summary = json.loads((training / "summary.json").read_text())
result = json.loads((evaluation / "evaluation.json").read_text())
config = json.loads((evaluation / "config.json").read_text())
assert hashlib.sha256((training / "model.json").read_bytes()).hexdigest() == config["model_sha256"]


def inspect(folder):
    with sqlite3.connect(folder / "observations.sqlite") as db:
        counts = dict(db.execute("SELECT kind,COUNT(*) FROM events GROUP BY kind"))
        words = {tuple(json.loads(row[0])) for row in db.execute("SELECT actions FROM experiments")}
        phases = dict(db.execute("SELECT phase,COUNT(*) FROM experiments GROUP BY phase"))
    return counts, words, phases


train_counts, train_words, train_phases = inspect(training)
eval_counts, eval_words, eval_phases = inspect(evaluation)
assert train_counts["action"] == summary["physical_costs"]["actions"] == 2004
assert train_counts["reset"] == summary["physical_costs"]["resets"] == 368
assert eval_counts["action"] == result["steps"] == 1492
assert eval_counts["reset"] == result["count"] == 100
assert len(eval_words) == 100
assert not train_words.intersection(eval_words)
assert eval_phases == {"held-out": 100}
assert train_phases == {"reset-check": 2, "training": 366}
print(
    json.dumps(
        {
            "audit": "PASS",
            "train_counts": train_counts,
            "evaluation_counts": eval_counts,
            "full_sequence_overlap": 0,
        },
        indent=2,
    )
)
