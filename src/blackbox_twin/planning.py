"""Transparent finite-model experiment ranking; no posterior or novelty claim."""

import random
import time
from collections import deque
from dataclasses import dataclass, field
from itertools import product


@dataclass
class PlanningContext:
    model: object
    history: dict = field(default_factory=dict)
    counterexamples: list = field(default_factory=list)
    remaining_actions: int = 0


@dataclass(frozen=True)
class Proposal:
    actions: tuple
    estimated_actions: int
    estimated_resets: int
    score: float
    reasons: tuple


def access_paths(model):
    paths, queue = {model.initial_state: ()}, deque([model.initial_state])
    while queue:
        state = queue.popleft()
        for action, edge in model.transitions[state].items():
            if edge.next_state not in paths:
                paths[edge.next_state] = paths[state] + (action,)
                queue.append(edge.next_state)
    return paths


def distinguishing_suffixes(model):
    """Shortest pairwise separators in this finite hypothesis, not in the target."""
    reachable = list(access_paths(model))
    suffixes = set()
    for index, left in enumerate(reachable):
        for right in reachable[index + 1 :]:
            queue, seen = deque([(left, right, ())]), {(left, right)}
            while queue:
                a, b, word = queue.popleft()
                for symbol in model.actions:
                    x, y = model.transitions[a][symbol], model.transitions[b][symbol]
                    if x.output != y.output:
                        suffixes.add(word + (symbol,))
                        queue.clear()
                        break
                    pair = (x.next_state, y.next_state)
                    if pair not in seen:
                        seen.add(pair)
                        queue.append((*pair, word + (symbol,)))
    return sorted(suffixes, key=lambda w: (len(w), w))


def features(model, word):
    state, transitions, contexts = model.initial_state, set(), set()
    for index, symbol in enumerate(word):
        transitions.add((state, symbol))
        contexts.add((state, tuple(word[max(0, index - 2) : index + 1])))
        state = model.transitions[state][symbol].next_state
    return transitions, contexts


class ExperimentPlanner:
    """Shared next-experiment interface for custom baselines and ranked variants."""

    def __init__(self, method="cost-aware", seed=7, pool_size=96, max_length=12):
        if pool_size < 1 or max_length < 1:
            raise ValueError("Candidate limits must be positive")
        self.method, self.rng = method, random.Random(seed)
        self.pool_size, self.max_length = pool_size, max_length
        self.enumeration_index = 0
        self.planning_seconds = 0.0
        self.selected = 0

    def _bfs_next(self, alphabet):
        # Lexicographic breadth-first base-k words; no hidden target metadata.
        number, length = self.enumeration_index, 1
        self.enumeration_index += 1
        while number >= len(alphabet) ** length:
            number -= len(alphabet) ** length
            length += 1
        if length > self.max_length:
            return None
        digits = []
        for _ in range(length):
            digits.append(alphabet[number % len(alphabet)])
            number //= len(alphabet)
        return tuple(reversed(digits))

    def candidates(self, context):
        model, alphabet = context.model, list(context.model.actions)
        if not alphabet:
            return []
        if self.method == "random":
            return [
                tuple(
                    self.rng.choice(alphabet) for _ in range(self.rng.randint(1, self.max_length))
                )
            ]
        if self.method == "bfs":
            word = self._bfs_next(alphabet)
            return [word] if word else []
        paths = list(access_paths(model).values())
        separators = distinguishing_suffixes(model)
        words = []
        for prefix in paths:
            for symbol in alphabet:
                words.append(prefix + (symbol,))
                if self.method != "no-suffix":
                    words.extend(prefix + (symbol,) + suffix for suffix in separators)
        # Generic repeated-symbol probes can challenge merged/self-loop control states.
        for length in range(2, self.max_length):
            for symbol, last in product(alphabet, repeat=2):
                words.append((symbol,) * length + (last,))
        # Shared finite pool cap: seeded proposals, plus explicit model-derived candidates.
        for _ in range(self.pool_size):
            prefix = self.rng.choice(paths)
            tail = tuple(
                self.rng.choice(alphabet) for _ in range(self.rng.randint(1, self.max_length))
            )
            words.append(prefix + tail)
        return list(dict.fromkeys(w for w in words if 0 < len(w) <= self.max_length))

    def propose(self, context):
        started = time.perf_counter()
        try:
            covered_edges, covered_contexts = set(), set()
            if self.method not in {"random", "bfs"}:
                for word in context.history:
                    edges, contexts = features(context.model, word)
                    covered_edges.update(edges)
                    covered_contexts.update(contexts)
            suffixes = distinguishing_suffixes(context.model) if self.method != "no-suffix" else []
            proposals = []
            for word in self.candidates(context):
                if word in context.history:
                    continue
                # Prefix reuse cannot save physical replay on a NEW full sequence.
                cost = len(word)
                if cost > context.remaining_actions:
                    continue
                edges, contexts = features(context.model, word)
                coverage = len(edges - covered_edges) + 0.25 * len(contexts - covered_contexts)
                suffix = float(any(len(w) <= len(word) and word[-len(w) :] == w for w in suffixes))
                utility = 1.0 + (0.0 if self.method == "no-coverage" else coverage) + 0.5 * suffix
                score = utility if self.method == "no-cost" else utility / (cost + 1)
                proposals.append(
                    Proposal(
                        word,
                        cost,
                        1,
                        score,
                        (
                            "unqueried-word",
                            f"new-coverage={coverage}",
                            f"hypothesis-separator={suffix}",
                            f"physical-replay={cost}",
                        ),
                    )
                )
            if not proposals:
                return None
            chosen = max(
                proposals,
                key=(lambda p: (p.score, p.actions))
                if self.method == "no-cost"
                else (lambda p: (p.score, -len(p.actions), p.actions)),
            )
            self.selected += 1
            return chosen
        finally:
            self.planning_seconds += time.perf_counter() - started


def planned_sequences(model, history, seed=7, count=100, max_length=12, remaining=6000):
    """M3 differential-loop integration; yielded words remain real reset/replay experiments."""
    planner = ExperimentPlanner(seed=seed, max_length=max_length)
    known = dict(history)
    for _ in range(count):
        proposal = planner.propose(PlanningContext(model, known, remaining_actions=remaining))
        if proposal is None:
            return
        yield proposal.actions
        known[proposal.actions] = True
        remaining -= proposal.estimated_actions
