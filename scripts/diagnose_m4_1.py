"""Bounded development diagnostics, historical trace analysis, and uninstrumented profile."""

import argparse
import cProfile
import json
import pstats
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import median

from blackbox_twin import benchmark
from blackbox_twin.benchmark_targets import RUNNER, generate_target
from blackbox_twin.contracts import Action, Target
from blackbox_twin.learning import serialize
from blackbox_twin.planner_diagnostics import DiagnosticPlanner
from blackbox_twin.planner_oracles import SelectionOracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence/m4-1"


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def historical():
    result = {}
    for method in ("cost-aware", "no-cost", "no-coverage", "no-suffix", "aalpy-state-prefix"):
        rows = []
        for path in sorted((ROOT / "evidence/m4-confirmatory").glob(f"*/*/{method}/attempt-000")):
            with sqlite3.connect(
                f"file:{(path / 'observations.sqlite').as_posix()}?mode=ro", uri=True
            ) as db:
                words = [
                    json.loads(w)
                    for (w,) in db.execute(
                        "SELECT actions FROM experiments WHERE phase='equivalence-search'"
                    )
                ]
                decisions = [
                    json.loads(w)
                    for (w,) in db.execute(
                        "SELECT content FROM artifacts WHERE kind='planner_decision'"
                    )
                ]
                timing = {
                    kind: seconds
                    for kind, seconds in db.execute(
                        "SELECT kind,SUM(elapsed) FROM events GROUP BY kind"
                    )
                }
            train = json.loads((path / "training.json").read_text())
            lengths = list(map(len, words))
            rows.append(
                {
                    "family": path.parts[-4],
                    "seed": path.parts[-3],
                    "experiments": len(words),
                    "length_median": median(lengths),
                    "length_histogram": dict(Counter(lengths)),
                    "selected_length_histogram": dict(
                        Counter(len(d["actions"]) for d in decisions)
                    ),
                    "decisions": len(decisions),
                    "counterexamples": train["counterexamples"],
                    "selected_coverage_nonzero": sum(
                        "new-coverage=0.0" not in d["reasons"] for d in decisions
                    ),
                    "selected_separator_nonzero": sum(
                        "hypothesis-separator=1.0" in d["reasons"] for d in decisions
                    ),
                    "elapsed_events": timing,
                    "costs": train["costs"],
                    "phase_costs": train["phase_costs"],
                }
            )
        result[method] = rows
    save(OUT / "historical.json", result)


class DiagnosticOracle(SelectionOracle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.planner = DiagnosticPlanner(
            self.method, args[3], kwargs["pool_size"], kwargs["max_length"]
        )
        self.pending = None
        self.ce_record = None
        original = self.planner.propose

        def propose(context):
            self.finish()
            before = len(self.planner.records)
            choice = original(context)
            if choice and len(self.planner.records) > before:
                self.pending = (self.planner.records[-1], self.session.costs.model_copy())
            return choice

        self.planner.propose = propose

    def finish(self):
        if self.pending:
            row, before = self.pending
            row["actual_actions"] = self.session.costs.actions - before.actions
            row["actual_resets"] = self.session.costs.resets - before.resets
            if not row["counterexample"]:
                row["changed_model"] = False
            self.pending = None

    def find_cex(self, hypothesis):
        if self.ce_record:
            self.ce_record["changed_model"] = self.ce_model != serialize(
                hypothesis, self.session.target.actions, {}
            ).model_dump(exclude={"provenance"})
            self.ce_record["states_after"] = len(hypothesis.states)
            self.ce_record = None
        try:
            found = super().find_cex(hypothesis)
            if found and self.pending:
                self.ce_record = self.pending[0]
                self.ce_model = serialize(hypothesis, self.session.target.actions, {}).model_dump(
                    exclude={"provenance"}
                )
                self.ce_record.update(counterexample=True, states_before=len(hypothesis.states))
            return found
        finally:
            self.finish()
            save(
                self.folder / "diagnostics.json",
                {"records": self.planner.records, "dropped": self.planner.dropped},
            )


def micro_target(folder):
    """Ordered rare path with expensive state access; evaluator-owned, no hidden-state logging."""
    folder.mkdir()
    pattern = "abacaba"
    table = []
    for i in range(len(pattern) + 1):
        table.append(
            {
                a: [
                    i + 1 if i < len(pattern) and a == pattern[i] else 0,
                    {"hit": i == len(pattern) and a == "c"},
                ]
                for a in "abc"
            }
        )
    script = folder / "oracle.py"
    script.write_text(RUNNER.replace("DATA", repr(json.dumps(table))), encoding="utf-8")
    target = Target(
        target_id="rare-ordered-access",
        version="1",
        executable="oracle.py",
        authorization="owned-local-fixture",
        actions={a: Action(operation=a) for a in "abc"},
    )
    save(folder / "target.json", target.model_dump())
    return target, script


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    OUT = parser.parse_args().out.resolve()
    OUT.mkdir()  # Refuse accidental overwrite.
    historical()
    config = {
        "budgets": [250, 500],
        "max_resets": 1000,
        "seconds_per_run": 60,
        "pool_size": 64,
        "max_length": 12,
    }
    save(
        OUT / "development-protocol.json",
        {
            "label": "DEVELOPMENT ONLY; no new confirmatory inference or weight tuning",
            "config": config,
            "maximum_training_actions": 6500,
            "targets": [
                "random-301",
                "delayed-301-depth4",
                "delayed-302-depth5",
                "rare-ordered-access",
            ],
            "selection_seeds": [400301, 400302],
            "evaluation": "none; discovery and costs only",
            "stopping": "11 diagnostic cells plus 2 uninstrumented profiling cells; then stop",
        },
    )
    summaries = []
    targets = []
    for family, seed in [("random", 301), ("delayed", 301), ("delayed", 302)]:
        targets.append(
            (
                f"{family}-{seed}",
                *generate_target(OUT / f"target-{family}-{seed}", family, seed),
                seed,
            )
        )
    targets.append(("rare-access", *micro_target(OUT / "target-rare-access"), 301))
    for name, target, script, seed in targets:
        methods = ["cost-aware", "aalpy-state-prefix"]
        if name == "delayed-302":
            methods += ["no-cost", "no-coverage", "no-suffix"]
        for method in methods:
            folder = OUT / f"{name}-{method}"

            def factory(*args, diagnostic_folder=folder, **kwargs):
                oracle = DiagnosticOracle(*args, **kwargs)
                oracle.folder = diagnostic_folder
                return oracle

            benchmark.SelectionOracle = factory
            result = benchmark.train_cell(target, script, folder, config, method, seed + 400000)
            summaries.append({"fixture": name, **result})
    benchmark.SelectionOracle = SelectionOracle
    name, target, script, seed = targets[2]
    profiles = {}
    for method in ("cost-aware", "aalpy-state-prefix"):
        profiler = cProfile.Profile()
        profiler.enable()
        result = benchmark.train_cell(
            target, script, OUT / f"profile-{method}", config, method, seed + 400000
        )
        profiler.disable()
        profiler.dump_stats(str(OUT / f"{method}.prof"))
        entries = []
        for (filename, line, function), (_cc, nc, exclusive, cumulative, _) in pstats.Stats(
            profiler
        ).stats.items():
            if "blackbox_twin" in filename:
                entries.append(
                    dict(
                        file=Path(filename).name,
                        line=line,
                        function=function,
                        calls=nc,
                        exclusive=exclusive,
                        cumulative=cumulative,
                    )
                )
        profiles[method] = {
            "training": result,
            "functions": sorted(entries, key=lambda r: r["exclusive"], reverse=True),
        }
    save(OUT / "profiles.json", profiles)
    save(OUT / "development.json", summaries)
    print(
        json.dumps(
            {
                "cells": len(summaries),
                "diagnostic_actions": sum(s["costs"]["actions"] for s in summaries),
                "profile_actions": sum(
                    p["training"]["costs"]["actions"] for p in profiles.values()
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
