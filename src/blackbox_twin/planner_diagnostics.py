"""Optional bounded development instrumentation; leaves frozen M4 scoring unchanged."""

import time
from collections import Counter

from .planning import ExperimentPlanner, access_paths, distinguishing_suffixes, features


class DiagnosticPlanner(ExperimentPlanner):
    def __init__(self, *args, limit=600, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = limit
        self.records = []
        self.dropped = 0
        self.pool = []

    def candidates(self, context):
        started = time.perf_counter()
        self.pool = super().candidates(context)
        self.generation_seconds = time.perf_counter() - started
        return self.pool

    def propose(self, context):
        chosen = super().propose(context)
        if len(self.records) >= self.limit:
            self.dropped += 1
            return chosen
        edges, contexts = set(), set()
        for word in context.history:
            e, c = features(context.model, word)
            edges.update(e)
            contexts.update(c)
        separators = distinguishing_suffixes(context.model)
        paths = access_paths(context.model)
        rows = []
        for word in self.pool:
            if word in context.history or len(word) > context.remaining_actions:
                continue
            e, c = features(context.model, word)
            coverage = len(e - edges) + 0.25 * len(c - contexts)
            suffix = float(any(word[-len(w) :] == w for w in separators))
            applied_coverage = 0 if self.method == "no-coverage" else coverage
            applied_suffix = 0 if self.method == "no-suffix" else 0.5 * suffix
            utility = 1 + applied_coverage + applied_suffix
            score = utility if self.method == "no-cost" else utility / (len(word) + 1)
            rows.append(
                dict(
                    actions=list(word),
                    cost=len(word),
                    coverage=coverage,
                    applied_coverage=applied_coverage,
                    separator=applied_suffix,
                    score=score,
                )
            )
        rows.sort(
            key=lambda r: (
                r["score"],
                0 if self.method == "no-cost" else -r["cost"],
                tuple(r["actions"]),
            ),
            reverse=True,
        )
        a = len(context.model.actions)
        structural = len(paths) * a * (1 + (len(separators) if self.method != "no-suffix" else 0))
        self.records.append(
            {
                "generated_before_length_filter_and_dedup": structural
                + max(0, self.max_length - 2) * a * a
                + self.pool_size,
                "unique_length_filtered": len(self.pool),
                "eligible": len(rows),
                "length_histogram": dict(Counter(r["cost"] for r in rows)),
                "coverage_nonzero": sum(r["coverage"] > 0 for r in rows),
                "separator_nonzero": sum(r["separator"] > 0 for r in rows),
                "reachable_states": len(paths),
                "access_lengths": list(map(len, paths.values())),
                "separators": [list(s) for s in separators],
                "top_candidates": rows[:12],
                "longest_candidate": max(rows, key=lambda r: r["cost"]) if rows else None,
                "selected": list(chosen.actions) if chosen else None,
                "score": chosen.score if chosen else None,
                "reasons": list(chosen.reasons) if chosen else [],
                "candidate_generation_seconds": self.generation_seconds,
                "actual_actions": None,
                "actual_resets": None,
                "counterexample": False,
                "changed_model": None,
            }
        )
        return chosen
