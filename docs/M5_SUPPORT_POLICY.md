# Evidence support policy — model version 3

Policy identifier: `m5.1-complete-bounded-consensus-v1`. Versions 1 and 2 retain their
historical execution behavior. Version 3 is the evidence-aware wallet model produced
by `bbt typed-harden`. Native StatePrefix remains the state-learning default; this is
bounded typed ambiguity resolution, not the experimental M4 cost-aware ranker.

## Status semantics

| Status | Required evidence / action |
|---|---|
| OBSERVED | Same concrete action at the same observable balance/frozen context was recorded from a real oracle run; contradictory duplicates reject compilation. Execute the recorded response/transition. |
| INFERRED_SUPPORTED | Within the declared finite grammar, every feasible guard function and compatible numeric update agrees on one applicable response and observed next state; supporting rules/observations and applicability cells are recorded. Public state-preserving validation errors are separately justified by the frozen public contract. |
| AMBIGUOUS | Feasible guards disagree, multiple response classes may apply, coverage may be absent in some candidates, or compatible updates disagree. Return an explicit ambiguous refusal. |
| UNSUPPORTED | Unobserved state/schema context, empty feasible model class, no response class, unobserved next state, malformed request, or session state already unknown. Return an explicit unsupported refusal. |

These are evidence metadata, **not probabilities or mathematical certainty about hidden
software**. Observed-state equivalence, determinism/reset, the discovered response
vocabulary and the restricted grammar are declared assumptions. A new error class,
unobserved hidden control state or nonconvex rule can falsify those assumptions. The
policy does not claim arbitrary-program correctness.

## Full bounded guard space

The existing grammar is retained: conjunctions of zero to three predicates
`amount + k*balance <= c` or `>= c`, k in {-1,0,1}, c in -12..12 for this contract.
The bounded analysis population includes every public balance 0..4 and amount -8..8,
separately per operation and frozen context. Zero-argument operations use amount 0.
Only actually observed state pairs receive executable support cells.

For each observed output skeleton, enumerate **all** eligible atoms and all conjunctions
of up to three atoms consistent with its positive and competing-class negative examples.
Deduplicate only functions identical on the **entire declared finite population**, not
functions merely identical on observed samples. There is no top-24/top-8 pruning in this
analysis. Repeated identical atoms cannot create a distinct function, so combination
enumeration over distinct atomic functions preserves the bounded grammar's behaviors.

For each class store the union (`may`) and intersection (`must`) of its feasible function
masks, function count, population ordering and witness expressions. These independent
class spaces overapproximate full models: overlaps/holes are not forced into a partition.
This can reduce coverage but cannot manufacture agreement. A non-observed point earns
INFERRED_SUPPORTED only when exactly one class both may and must apply, no competing
class may apply, every surviving update gives the same output and its next state has
been observed. One rule existing or winning a regularizer is insufficient.

Updates remain `keep`, `add amount`, `subtract amount`, or `assign c` for c in 0..4.
All expressions fitting the evidence survive. No update is selected for convenience;
disagreement at the queried point is an ambiguity. Python integer arithmetic is exact;
out-of-state results cannot become supported concrete transitions. No Z3 or unrestricted
expression evaluator is needed. Enumeration evaluates model hypotheses, not the oracle.

## Provenance and concrete fallback

The root model stores its version, semantic model ID, observations once, and refinement
history. Rules have stable IDs, model version, operation/control context, output skeleton,
all compatible updates, supporting observation indices, boundary-observation references,
candidate partition masks, witness guards, known counterexample/history references,
contradiction field and explicit support-region references. A rule's evidence-status
summary never grants support to its entire may-region; the point-specific status governs.
Every observation's experiment ID resolves to SQLite request/response records. The audit
reconciles these references and rebuilds the complete support model.

Cells index the finite applicability region and reference rule IDs/evidence. This is
compilation of inferred functions, not exhaustive target querying or a claim to general
register learning. Adjacent tested values and all relevant state/value samples remain
available through rule observation indices; large raw traces are not repeated per rule.

Direct same-state/action observations take precedence as a concrete fallback. They do
not come from the baseline's predictions or evaluator answers, and observations from
another state are not substituted. If the broader grammar is unrepresentable, concrete
observations remain useful while untested regions refuse. Contradictory observations
reject compilation rather than being resolved by priority.

## Runtime and compatibility

Normal stdout remains the exact original-style JSON for concrete predictions. A refusal
contains `bbt_unsupported: true`, `support_status: AMBIGUOUS|UNSUPPORTED` and a reason.
It is distinct from a target-style `status:error` response. `--explain` emits an envelope
with `output` and `support`, including model ID/version, status, reason and evidence/rule
references. This optional mode is not used for target-fidelity scoring.

After any valid unknown-effect action, or malformed request, session state becomes unknown.
Every subsequent action refuses until the exact trusted reset message restores (0,false).
The runtime cannot query the original, infer a balance from its own refusal, or silently
carry an old state forward. Public validation errors are different: the frozen contract
explicitly specifies their response and state preservation. Thus unknown-operation,
wrong-type and out-of-domain validation errors can preserve known state under that public
contract; an in-domain action with unknown effect cannot.

Version 3 embeds only standard-library runtime code and the learned support model. It
needs no original program, training database, external service or BBT installation.
Older model formats and CLI commands remain available for reproducibility; their outputs
must not be relabelled as version-3-supported without conversion and validation.

## Resolution and stopping

Start with the same fixed-grid L*/StatePrefix observations as the baseline. Construct
shortest access paths using actual observed transitions. Select only ambiguous,
unobserved, permitted state/action points; prefer the shortest physical replay, with
independently seeded tie-breaking. This is a bounded distinguishing-experiment schedule,
not a utility/coverage score or M4 planner. Replay the full access sequence and charge
reset plus every action. Recompile after each observation and record the parent model,
query, actual cost and physical experiment reference.

Fresh protocol cap: 12 distinguishing probes inside a total 5,000-action/1,000-reset/120-s
arm budget, including the seed and final original/twin regression replays. If no permitted
probe distinguishes the remaining cases, or the cap/budget prevents it, retain ambiguity.
No oracle calls occur at twin runtime. Symbolic references, hidden registers, arbitrary
schemas and infinite-domain reasoning remain outside this policy.

## Metrics

Concrete output coverage = concrete outputs / all evaluated outputs. Conditional accuracy
= correct concrete outputs / concrete outputs. False-supported rate = wrong concrete
outputs / concrete outputs. For legacy models, concrete output is their *implicit*
support claim, not a retroactive version-3 label. Abstention rate counts both ambiguous
and unsupported outputs over all outputs. Empty concrete denominators return null, not 1.
Trace fidelity compares complete raw JSON traces over **all** sequences. Sequence coverage
and conditional complete-trace accuracy are also reported. Refusals are not successful
matches unless the original genuinely emitted identical observable JSON.

Guard precision/recall use the exhaustive reachable-state transaction population, positive
when target status=ok. Abstentions are non-acceptance and therefore reduce recall.
Wrong target-style error predictions still reduce output accuracy even if acceptance
classification happens to agree. Good precision or conditional accuracy alone is never
reported as evidence of good end-to-end fidelity or broad coverage.
