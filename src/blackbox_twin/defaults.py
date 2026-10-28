"""Recommended finite-state CLI policy; experimental strategies remain explicit options."""

from aalpy.oracles import RandomWMethodEqOracle, StatePrefixEqOracle

from .planner_oracles import ReplayCacheSUL, SelectionOracle

DEFAULT_STRATEGY = "aalpy-state-prefix"
STRATEGIES = (
    DEFAULT_STRATEGY,
    "aalpy-random-w",
    "random",
    "bfs",
    "cost-aware",
    "no-cost",
    "no-coverage",
    "no-suffix",
)


def learning_options(strategy=DEFAULT_STRATEGY, seed=7, walks=25, walk_length=12):
    if strategy not in STRATEGIES:
        raise ValueError("Unknown learning strategy")

    def factory(alphabet, sul):
        if strategy in {"aalpy-state-prefix", "aalpy-random-w"}:
            cls = StatePrefixEqOracle if strategy == DEFAULT_STRATEGY else RandomWMethodEqOracle
            # Finite sampled search; unlike the benchmark, do not repeat to spend the budget.
            return cls(alphabet, sul, walks_per_state=walks, walk_len=walk_length)
        return SelectionOracle(alphabet, sul, strategy, seed, max_length=walk_length)

    return {
        "equivalence_factory": factory,
        "sul_factory": ReplayCacheSUL,
        "provenance": {"method": strategy, "search": "finite sampled; no equivalence proof"},
    }
