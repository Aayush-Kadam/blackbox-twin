# M5 bounded typed/guard model

Historical version-2 specification. M5.1 adds version 3 with complete bounded candidate
spaces and explicit evidence statuses; see `M5_SUPPORT_POLICY.md`. Version-2 behavior
and its original results below remain unchanged for reproducibility.

Model version **2**, alongside unchanged finite Mealy model version 1. The supported
problem is deterministic local resettable software with integer amount inputs in -8..8,
observable integer balance in 0..4 and observable Boolean frozen state. The sufficiency
of `(balance,frozen)` is a checked hypothesis, not a property inferred for arbitrary
hidden software. Conflicting outputs for the same contextual action fail closed.

## Input and state representation

The existing `Action(operation, arguments)` is retained. `typed.py` adds strict integer,
Boolean, enum and optional/nullable field schemas, canonical JSON identity, and registration
in the existing finite `Target.actions` map. The key includes the contract identifier;
JSON true, 1 and 1.0 have different keys. `Session`, SQLite events, AALpy replay caches,
M3 comparisons and ddmin still use their existing symbolic words, now mapped to concrete
typed actions. Novel suffixes still pay complete physical prefix replay. There is no
cache keyed merely by an inferred value partition. Guard fitting itself uses observations,
not a persistent abstraction cache, so a revised guard cannot silently reuse its own predictions.

The learner records reset-based access sequences and all actual outputs. Initial StatePrefix
L* uses the 13-symbol fixed alphabet: two operations times five amounts, plus three
zero-argument operations. Its initial phase has a 1,000-action ceiling inside the shared
5,000-action budget. Actual runs reached this ceiling; no completed finite-learning
convergence is claimed. A common fixed-grid state-cover pass then completes missing
contextual grid observations in newly observed states. This pass is identical for both
methods. Final guarded states come from observable outputs, not a claim that L* synthesized
a register automaton. There are 10 observed `(balance,frozen)` pairs in eval-a and 8 in eval-b.

## Restricted hypothesis grammar

Each rule has an operation, prior frozen context, a conjunction of at most three inferred
predicates, a fixed output skeleton and compatible balance updates. Predicate grammar:

```text
amount + k * balance <= c
amount + k * balance >= c
k in {-1,0,1}, c in {-12,...,12}
```

Equality and intervals can be expressed by two inequalities. Boolean frozen context is
selected from actual observations. Output skeletons (status, error string when present,
and following frozen value) are discovered by grouping actual responses with only balance
removed. Meaningful numerical balances are never normalized away.

Update grammar is exactly `keep`, `add amount`, `subtract amount`, or `assign c` for a
constant c in 0..4. Every retained update fits every supporting sample. Multiple retained
updates must agree at runtime; otherwise the result is explicitly unsupported. A resulting
state must already have been observed. No arbitrary expressions, eval, solver or target
source are used. This arithmetic grammar is an explicit inductive bias, not a wallet
rule inserted after inspecting evaluation outputs.

Guard fitting enumerates finite atomic candidates that accept all observations of a
response class. Atoms are deduplicated by coefficient, direction and excluded-negative
set; the representative cut prefers the midpoint of observed contrasting endpoints.
At most 24 candidate atoms participate in a one-, two-, or three-term set-cover search.
Ordering prefers fewer terms, fewer state-dependent terms, midpoint proximity, then
deterministic JSON order. Up to eight consistent conjunctions are recorded. They are a
bounded candidate set, not an exhaustive posterior; deduplication can collapse different
untested cuts into one representative. No confidence probability is manufactured.

Boundary experiments enumerate the *model's* predictions over allowed values, selecting
unobserved contextual values near candidate boundaries, differing alternatives or uncovered
regions. They execute real reset/access/action experiments, with up to 16 probes per round
and three rounds. Reserved values are never probed. This is neither binary search nor an
assumption that arbitrary target behavior is monotone. A single conjunctive class cannot
represent arbitrary holes/disjunctions; an inconsistent fit is reported as unrepresentable.

## Evidence and support semantics

Each rule records sample indices, exact tested values, retained update candidates,
competing conjunctions, adjacent-boundary sample references, and untested values per
balance/frozen context. The model carries full observations, access sequences and revision
provenance. Known discrepancies and their complete/minimized traces are preserved in
the run's `counterexample.json`, linked to immutable revision-000 and later model/twin
directories. The training receipt links final model and replay results. Samples include
original experiment IDs, so response evidence can be reconciled to committed SQLite events.

These are empirical hypotheses with tested support and explicit untested regions. The
regularizer selects one observationally consistent guard set; alternative guard predictions
do not all have to agree before execution. Consequently underdetermined boundaries can
still give an incorrect answer. Runtime abstention covers overlapping/uncovered *selected*
guards, ambiguous updates, unobserved state and malformed inputs; it does not solve all
observational ambiguity. This is a material M5 limitation demonstrated by eval-b.

Public schema violations yield the frozen contract's exact validation error and preserve
state. Twin-unsupported results carry `bbt_unsupported: true`, separately classified by
M3 comparison. After a valid but unsupported action, state becomes unknown until reset,
since its actual update is unknown. This can propagate unsupported outputs through a
long sequence; it avoids fabricating a subsequent balance. Symbolic reference binding,
general register inference, hidden numeric-state discovery and infinite domains are unsupported.

## Demonstrated capability levels

- **A — concrete:** both methods reconstruct the fixed grid with real finite-state learning
  and observable-context completion.
- **B — partitions:** unseen negative and high positive values are covered by learned
  guarded regions, independently tested without passing their outputs back to training.
- **C — restricted observable-state relation:** eval-a learns deposit success as
  `amount >= 1`, `amount <= 3`, `amount + balance <= 4`, with balance update `add`;
  withdrawal success uses `amount >= 1`, `amount <= 3`, `amount - balance <= 0`, with
  `subtract`. These forms/constants are fitted from real observations, not ground truth.
  Amount 2 never occurs in training and is correctly executed in all evaluator contexts
  for this configuration. This supports only these bounded observable-state guards,
  not general register-automata synthesis or universal Capability C.

Eval-b demonstrates that a different consistent relation/cut can survive the same probe
policy and fail at unseen amount 2. Finite state enumeration alone is not called guard
generalization; the unobserved argument tests and arithmetic outputs are essential evidence.

## Standalone generation and refinement

`synthesis.generate_twin` dispatches model versions while preserving finite generation.
Version 2 embeds the serialized learned model and dependency-free `typed_runtime.py`.
It imports only Python standard library code and needs no target, database or package.
The independently installed reproduction executed the generated file from a directory
containing only that file, with Python `-I -S`.

M5 uses existing `DifferentialRunner`, full original/twin traces, JSON-pointer differences,
physical sessions and M3 `minimize`. A semantic filter retains the original target outcome
class and differing fields during deletion. Bounded argument shrinking tries smaller
allowed integers, replays both processes, and accepts only the same failure semantics.
Reserved values and invalid dependencies are not silently introduced. Shrinking is local,
not globally minimal. All shrink attempts and failed proposals remain charged evidence.
Refinement reads new original observations, refits guards, regenerates the twin, replays
the minimized failure and every distinct previously observed contextual experiment.
