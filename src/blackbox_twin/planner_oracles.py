"""Fair common SUL cache and exchangeable established/custom equivalence search."""

import json
import time

from aalpy.base import SUL, Oracle
from aalpy.oracles import RandomWMethodEqOracle, StatePrefixEqOracle

from .learning import serialize
from .oracle import OracleFailure
from .planning import ExperimentPlanner, PlanningContext


def encode(observation):
    return json.dumps(observation.payload, sort_keys=True, separators=(",", ":"))


class ReplayCacheSUL(SUL):
    """All methods reuse complete observed prefixes; NEW suffixes replay the ENTIRE path."""

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.history = {}
        self.word, self.outputs, self.active = [], [], False
        self.cache_actions, self.cache_traces, self.adapter_seconds = 0, 0, 0.0
        session.replay_cache = self

    def pre(self):
        started = time.perf_counter()
        self.post()
        self.session.check("clock")
        self.word, self.outputs, self.active = [], [], False
        self.adapter_seconds += time.perf_counter() - started

    def step(self, letter):
        started = time.perf_counter()
        try:
            word = tuple(self.word + [letter])
            if not self.active and word in self.history:
                output = self.history[word][-1]
                self.cache_actions += 1
            else:
                if not self.active:
                    self.session.pre()
                    self.active = True
                    for index, previous in enumerate(self.word):
                        replayed = encode(self.session.step(previous))
                        if replayed != self.outputs[index]:
                            raise OracleFailure("nondeterminism_on_cached_prefix_replay")
                output = encode(self.session.step(letter))
            self.word.append(letter)
            self.outputs.append(output)
            if word in self.history and self.history[word] != self.outputs:
                raise OracleFailure("nondeterminism_in_replay_cache")
            self.history[word] = list(self.outputs)
            return output
        finally:
            self.adapter_seconds += time.perf_counter() - started

    def post(self):
        if self.active:
            self.session.post()
        elif self.word:
            self.cache_traces += 1
        self.active = False
        self.word, self.outputs = [], []


class SelectionOracle(Oracle):
    def __init__(self, alphabet, sul, method, seed, pool_size=96, max_length=12):
        super().__init__(alphabet, sul)
        self.method, self.session = method, sul.session
        self.planner = ExperimentPlanner(method, seed, pool_size, max_length)
        self.counterexamples = []
        self.batches, self.planning_seconds = 0, 0.0
        self.max_length = max_length

    def find_cex(self, hypothesis):
        call_started = time.perf_counter()
        adapter_started = self.session.replay_cache.adapter_seconds
        previous_phase = self.session.phase
        self.session.phase = "equivalence-search"
        try:
            if self.method in {"aalpy-random-w", "aalpy-state-prefix"}:
                while self.batches < 1000:
                    self.session.check("clock")
                    cls = (
                        RandomWMethodEqOracle
                        if self.method == "aalpy-random-w"
                        else StatePrefixEqOracle
                    )
                    native = cls(
                        self.alphabet, self.sul, walks_per_state=25, walk_len=self.max_length
                    )
                    try:
                        found = native.find_cex(hypothesis)
                    finally:
                        self.num_queries += native.num_queries
                        self.num_steps += native.num_steps
                    self.batches += 1
                    if found:
                        self.counterexamples.append(list(found))
                        return found
                return None
            model = serialize(hypothesis, self.session.target.actions, {})
            misses = 0
            while misses < 1000:
                self.session.check("clock")
                context = PlanningContext(
                    model,
                    self.session.replay_cache.history,
                    self.counterexamples,
                    self.session.budget.max_actions - self.session.costs.actions,
                )
                proposal = self.planner.propose(context)
                if proposal is None:
                    misses += 1
                    # A ranked pool has no affordable new word; do not spin or pad costs.
                    if self.method not in {"random", "bfs"}:
                        return None
                    continue
                misses = 0
                self.session.recorder.artifact(
                    "planner_decision",
                    {
                        "method": self.method,
                        "actions": list(proposal.actions),
                        "estimated_actions": proposal.estimated_actions,
                        "estimated_resets": proposal.estimated_resets,
                        "score": proposal.score,
                        "reasons": list(proposal.reasons),
                        "remaining_actions": context.remaining_actions,
                    },
                )
                self.sul.pre()
                hypothesis.reset_to_initial()
                self.num_queries += 1
                try:
                    for index, letter in enumerate(proposal.actions):
                        actual = self.sul.step(letter)
                        expected = hypothesis.step(letter)
                        self.num_steps += 1
                        if actual != expected:
                            found = proposal.actions[: index + 1]
                            self.counterexamples.append(list(found))
                            return found
                finally:
                    self.sul.post()
            return None
        finally:
            self.planning_seconds += max(
                0.0,
                time.perf_counter()
                - call_started
                - (self.session.replay_cache.adapter_seconds - adapter_started),
            )
            self.session.phase = "refinement-membership" if self.counterexamples else previous_phase
