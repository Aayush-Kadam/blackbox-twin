"""Established random and bounded state-cover extension experiment policies."""

import random
from collections import deque
from itertools import product


def random_sequences(alphabet, seed=7, count=200, min_length=1, max_length=12):
    if count < 0 or not 1 <= min_length <= max_length:
        raise ValueError("Invalid random sequence configuration")
    rng = random.Random(seed)
    for _ in range(count):
        yield tuple(rng.choice(alphabet) for _ in range(rng.randint(min_length, max_length)))


def state_cover(model):
    paths = {model.initial_state: ()}
    queue = deque([model.initial_state])
    while queue:
        state = queue.popleft()
        for symbol, transition in model.transitions[state].items():
            if transition.next_state not in paths:
                paths[transition.next_state] = paths[state] + (symbol,)
                queue.append(transition.next_state)
    return list(paths.values())


def guided_sequences(model, depth=5, count=1000, max_length=20):
    if depth < 1 or count < 0 or max_length < 1:
        raise ValueError("Invalid bounded state-cover configuration")
    emitted, seen = 0, set()
    # State access sequences followed by bounded alphabet extensions, breadth first.
    # This is not the complete W-method and has no conformance guarantee.
    for length in range(1, min(depth, max_length) + 1):
        for prefix in state_cover(model):
            for suffix in product(model.actions, repeat=length):
                word = prefix + suffix
                if len(word) > max_length or word in seen:
                    continue
                if emitted >= count:
                    return
                seen.add(word)
                emitted += 1
                yield word


def discover(runner, candidates):
    for word in candidates:
        result = runner.run(word)
        if result.status != "agreement":
            return result
    return None
