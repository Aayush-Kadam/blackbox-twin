"""Read-only, allowlisted projections of real persisted experiment evidence."""

import hashlib
import json
import re
import sqlite3
from pathlib import Path

from .contracts import BehavioralModel
from .m51 import predict_trace, shortest_access
from .support import SupportedModel
from .support_runtime import supported_step


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Evidence path leaves the allowlisted root")
    return path


def db_counts(path, twin=False):
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        values = dict(
            db.execute(
                "SELECT e.kind,COUNT(*) FROM events e JOIN experiments x ON x.id=e.experiment_id "
                "WHERE (x.phase LIKE 'twin:%')=? GROUP BY e.kind",
                (int(twin),),
            )
        )
    return {"actions": values.get("action", 0), "resets": values.get("reset", 0)}


class Evidence:
    def __init__(self, project: Path, runs: Path):
        self.project, self.runs = project.resolve(), runs.resolve()
        self.m6 = contained(self.project, "evidence/m6-confirmatory-v1")

    def project_file(self, name):
        return contained(self.project, name)

    def folder(self, experiment):
        if experiment == "m3-replay":
            return self.project_file("evidence/m3-demo")
        if re.fullmatch(r"live-[a-f0-9]{32}", experiment):
            path = contained(self.runs, experiment)
            if path.is_dir():
                return path
        raise KeyError("Unknown allowlisted experiment")

    def experiments(self):
        values = [
            {
                "id": "m3-replay",
                "label": "Delayed commit · historical M3 replay",
                "mode": "persisted replay",
            }
        ]
        if self.runs.exists():
            for path in sorted(self.runs.glob("live-*")):
                if not path.resolve().is_relative_to(self.runs):
                    continue
                if (
                    re.fullmatch(r"live-[a-f0-9]{32}", path.name)
                    and contained(path, "receipt.json").exists()
                ):
                    values.append(
                        {
                            "id": path.name,
                            "label": "Delayed commit · " + path.name[-8:],
                            "mode": "fresh executable demonstration",
                        }
                    )
        return values

    def model_path(self, experiment, revision, kind="model"):
        folder = self.folder(experiment)
        revisions = read(contained(folder, "loop/summary.json"))["revisions"]
        if revision < 0 or revision >= len(revisions):
            raise KeyError("Unknown revision")
        record = revisions[revision]
        expected = f"revisions/{revision:03d}/" + ("model.json" if kind == "model" else "twin.py")
        if record[kind] != expected:
            raise ValueError("Revision export path does not match its declared revision")
        path = contained(folder, "loop/" + record[kind])
        if sha(path) != record[kind + "_file_sha256"]:
            raise ValueError("Revision artifact integrity mismatch")
        return path

    def detail(self, experiment):
        folder = self.folder(experiment)
        summary = read(contained(folder, "loop/summary.json"))
        with sqlite3.connect(
            contained(folder, "loop/observations.sqlite").as_uri() + "?mode=ro", uri=True
        ) as db:
            configuration = json.loads(
                db.execute("SELECT metadata FROM runs ORDER BY rowid LIMIT 1").fetchone()[0]
            )
        models = []
        for index, _ in enumerate(summary["revisions"]):
            path = self.model_path(experiment, index)
            model = BehavioralModel.model_validate(read(path)).model_dump()
            models.append(
                {
                    "revision": index,
                    "model": model,
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                    "source": path.relative_to(folder).as_posix(),
                }
            )
        physical = db_counts(contained(folder, "loop/observations.sqlite"))
        if physical != {k: summary["original_costs"][k] for k in physical}:
            raise ValueError("Training receipt differs from physical event accounting")
        evaluation = read(contained(folder, "evaluation/evaluation.json"))
        records = [
            read(contained(folder, p.relative_to(folder)))
            for p in sorted(contained(folder, "loop/counterexamples").glob("*/discovery.json"))
        ]
        return {
            "id": experiment,
            "mode": "persisted replay"
            if experiment == "m3-replay"
            else "fresh executable demonstration",
            "summary": summary,
            "models": models,
            "evaluation": evaluation,
            "counterexamples": records,
            "physical_training": physical,
            "configuration": configuration,
            "fixture": "owned delayed-commit JSON-lines process",
            "input_contract": models[0]["model"]["actions"],
            "source": str(folder.relative_to(self.project))
            if folder.is_relative_to(self.project)
            else "operator-selected local demo output",
            "equivalence_proven": False,
        }

    def events(self, experiment, offset, limit):
        path = contained(self.folder(experiment), "loop/observations.sqlite")
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            total = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT e.*,x.phase FROM events e JOIN experiments x ON x.id=e.experiment_id "
                    "ORDER BY e.id LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            ]
        for row in rows:
            row["request"], row["response"] = (
                json.loads(row["request"]),
                json.loads(row["response"]),
            )
        return {"total": total, "offset": offset, "limit": limit, "rows": rows}

    def typed_model(self):
        folder = self.project_file(
            "evidence/m6-confirmatory-v1/B-wallet-1/seed-1-hardened-1500/training/attempt-000"
        )
        path = self.project_file(folder.relative_to(self.project) / "scored.json")
        integrity = read(self.project_file(folder.relative_to(self.project) / "integrity.json"))
        if sha(path) != integrity["scored.json"]:
            raise ValueError("Typed artifact integrity mismatch")
        model = SupportedModel.model_validate(read(path)).model_dump()
        return model, path

    def typed(self):
        model, path = self.typed_model()
        accesses, examples = shortest_access(model["observations"]), {}
        for key in model["cells"]:
            b, f, op, amount = json.loads(key)
            prefix = accesses.get((b, f))
            if prefix is None:
                continue
            action = {
                "operation": op,
                "arguments": {"amount": amount} if op in {"deposit", "withdraw"} else {},
            }
            actions = [*prefix, action]
            _, metadata = predict_trace(model, actions)
            status = metadata[-1]["status"]
            if status not in examples or len(actions) < len(examples[status]["actions"]):
                examples[status] = {"status": status, "actions": actions}
        if "AMBIGUOUS" in examples:
            examples["UNSUPPORTED"] = {
                "status": "UNSUPPORTED",
                "actions": [
                    *examples["AMBIGUOUS"]["actions"],
                    {"operation": "get_balance", "arguments": {}},
                ],
            }
        return {
            "model_id": model["model_id"],
            "schema_version": 3,
            "source": path.relative_to(self.project).as_posix(),
            "sha256": sha(path),
            "examples": list(examples.values()),
            "states": model["states"],
            "observations": len(model["observations"]),
            "rules": len(model["rules"]),
            "scope": "Saved M6 wallet support policy; preview makes zero new oracle queries.",
        }

    def preview(self, requests):
        model, _ = self.typed_model()
        state, rows = (0, False), []
        for action in requests:
            before = state
            if action == {"control": "reset"}:
                state, output = (0, False), {"control": "reset", "ok": True}
                support = {"status": "RESET", "reason": "trusted reset contract"}
            else:
                state, output, support = supported_step(model, state, action)
            rules = [
                {
                    k: rule[k]
                    for k in (
                        "rule_id",
                        "operation",
                        "output",
                        "updates",
                        "evidence",
                        "boundary_observations",
                        "refinement_history",
                    )
                }
                for rule in model["rules"]
                if rule["rule_id"] in support.get("rule_ids", [])
            ]
            indices = sorted(
                set(support.get("observation_indices", []))
                | {i for rule in rules for i in rule["evidence"]}
            )
            evidence = [model["observations"][i] for i in indices[:20]]
            rows.append(
                {
                    "action": action,
                    "state_before": before,
                    "state_after": state,
                    "output": output,
                    "support": support,
                    "evidence": evidence,
                    "rules": rules,
                    "evidence_total": len(indices),
                    "evidence_truncated": len(indices) > 20,
                }
            )
        return {
            "rows": rows,
            "oracle_actions": 0,
            "mode": "saved policy preview",
            "note": "Refusals are not target outputs or correct reconstruction.",
        }

    def benchmarks(self):
        results = read(self.project_file("evidence/m6-confirmatory-v1/results.json"))
        protocol = read(self.project_file("evidence/m6-confirmatory-v1/protocol.json"))
        cells = []
        for result in results:
            for point in result["points"]:
                cells.append(
                    {k: result[k] for k in ("target", "track", "family", "method", "learner_index")}
                    | {
                        "ceiling": point["ceiling"],
                        "actual_actions": point["actual_actions"],
                        "resets": point.get("actual_resets", result["training"]["costs"]["resets"]),
                        "learner_seed": protocol["learner_seeds"][result["learner_index"]],
                        "wall_seconds": result["training"]["wall_seconds"],
                        "model_bytes": point["model_bytes"],
                        "status": result["training"]["status"],
                        "metrics": point["metrics"]["overall"],
                        "criterion_reached": point["criterion_reached"],
                        "source": result["training_folder"],
                        "evaluation_source": point["evaluation_folder"],
                    }
                )
        return {
            "summary": read(self.project_file("evidence/m6-confirmatory-v1/summary.json")),
            "distinct_targets": len({r["target"] for r in results}),
            "cells": cells,
            "source": "evidence/m6-confirmatory-v1/results.json",
            "sha256": sha(self.m6 / "results.json"),
            "warning": (
                "Repeated seeds/checkpoints are not independent targets. Exhaustive diagnostics "
                "overlap training. Inventory refusals do not demonstrate reconstruction."
            ),
        }
