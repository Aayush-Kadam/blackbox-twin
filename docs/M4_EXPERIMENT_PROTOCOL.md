# M4 frozen pilot protocol

Original pilot frozen before its seeds ran: `benchmarks/manifests/m4-pilot.json`.
Primary confirmatory protocol: `benchmarks/manifests/m4-confirmatory.json`.
The suite records its hash and a digest of training, fixture-generation and metric code.
Resume rejects a changed manifest or implementation. Development used seeds 11/12;
the initial pilot used paired seeds 101–105. Review noticed that generation and selection
shared the same numeric seed. Its complete 120-cell negative result and audited source
snapshot are retained, not discarded. A fresh confirmatory block uses target seeds 201–205,
selection seeds 100201–100205, and evaluation seeds 200201–200205. Explicit seed separation
is the only methodological correction: weights, baselines, budgets, metrics and families
were not retuned. No score/weight tuning follows evaluation results.

## Method comparison and prior art

Official sources checked 2026-10-27: [AALpy](https://github.com/DES-Lab/AALpy),
[LearnLib](https://learnlib.de/). Installed AALpy 2.0.0 source/signatures were inspected.
Mealy learning, state/transition covers, characterizing suffixes, random words/walks,
counterexample processing and query caching are established methods. LearnLib lists these
families and abstraction facilities; no missing-capability or algorithmic-novelty claim is made.

| Method | Actual implementation and parameters | Expected strength / weakness |
|---|---|---|
| `random` | IID uniform length 1–12, IID uniform symbols; reject cached/unaffordable proposals | Broad exploration; can miss rare/deep paths |
| `bfs` | Lexicographic breadth-first finite words, lengths <=12 | Systematic coverage; exponential depth cost |
| `aalpy-random-w` | Installed RandomWMethodEqOracle, 25 walks/state, tail length <=12, characterizing suffix | Credible established model-guided baseline; long/repeated paths cost actions |
| `aalpy-state-prefix` | Installed StatePrefixEqOracle, 25 walks/state, 12-step walks, default depth-first order | State-access-guided baseline; no guarantee of finding hidden distinctions |
| `cost-aware` | Explicit candidate pool; new transition/three-input-context coverage plus hypothesis separators, divided by replay length + reset cost | Transparent cheap-test preference; potentially blind to long aliases/deep hidden states |
| `no-cost` | Same utility, no denominator or length tie preference | Tests whether short-query preference helps; longer probes may win |
| `no-coverage` | Remove transition/context contribution | Tests actual coverage component |
| `no-suffix` | Remove separator generation and suffix bonus | Tests actual distinguishing-suffix component |

Native finite test batches restart after a no-counterexample result until the same global
budget/guard is met. Their candidate selection remains installed library code. They may
append state-access and characterization strings beyond the 12-symbol random tail; all
such actions are charged. Custom word length is capped at 12. All have a 100-action hard
sequence cap and identical physical reset/action/time limits. This policy difference is
explicit; no alleged oracle equivalence or formal conformance guarantee is inferred.

## Proposed score, inputs and ablations

Candidate generation uses reachable learned-state access paths, outgoing symbols, learned
pairwise separating suffixes, generic repeated-symbol probes and 64 seeded random extensions.
Duplicates, cached full words and unaffordable candidates are excluded. No target operation
names are recognized specially. Unreachable learned states provide no access prefix.

Utility = 1 + new learned transitions + 0.25 * new three-input contexts + 0.5 * suffix bonus.
Rank = utility / (physical replay actions + 1 reset). Weights are fixed in the manifest and
implementation. Ties prefer shorter then lexicographically descending words; `no-cost`
uses only utility and lexicographic tie-breaking. The context history comes exclusively
from actual observations. These coverage proxies are heuristics, not information gain,
uncertainty probabilities or a hypothesis committee. A closed L* table often already covers
all learned transitions, so that component may be inactive. Such inactivity is reported,
not presented as evidence of useful exploration. Counterexample-derived generation and
model committees are deferred; no ablation is claimed for an unimplemented feature.

## Common learner, cache and accounting

Every method uses the same AALpy L*, RS counterexample processing, model representation,
owned JSON-lines process and Session physical counters/SQLite events. Each cell has fresh
process, reset validation, observation DB, learner and caches. Confirmed counterexamples
refine the actual L* hypothesis through its equivalence-oracle interface.

All methods share the same lazy prefix replay cache: an entirely observed word can return
recorded outputs without physical calls. Reaching any new suffix triggers a real reset and
replays **every** preceding action before continuing; no free prefix teleportation is allowed.
Replayed outputs are checked for consistency. AALpy membership-cache hits, cached prefix
outputs and complete virtual traces are separate logical counters, never subtracted from
physical counts. Baselines receive the same cache policy; differences are not attributed to
granting the proposed method an exclusive cache.

The comparative track isolates equivalence experiment selection inside streaming L*.
It does not execute M3's separate shrink/relearn/regression loop for any method; those phases
therefore cost zero in this track. Initial membership, reset validation, all equivalence tests
and subsequent refinement-membership calls are charged. The proposed planner separately
integrates with the full M3 differential/shrinking/refinement/export path in a real integration
test; its costs must not be confused with this comparative track.

All methods use per-event committed SQLite WAL with synchronous NORMAL, selected after a
development recording profile. This preserves committed events on ordinary process failure;
it is not a guarantee against hardware/power loss. M3's default recording mode is unchanged.
Planning/bookkeeping time subtracts timed adapter pre/step sections for all methods;
post/record bookkeeping can remain in that timer. Proposed scoring compute is also
measured separately. Total training wall time includes storage/export and
inference overhead. Native and custom methods incur their real instrumentation costs.

## Families, pairing and held-out separation

Random: five seeded reachable ring-backed Mealy machines with 4–6 states, 3 inputs and
3 output symbols. Delayed: thresholds 4,5,6,3,4 (four distinct variants, one repeated).
Workflow: the existing six-state order-processing fixture, reused across selection seeds.
Thus there are **15 paired configurations, 10 distinct generated oracle programs**, not
15 independent workflow implementations. Five selection seeds are used within each family.

For each pair, 80 distinct words of lengths 24–32 are frozen and reference outputs obtained
in a separate evaluator **before** any method trains. Every method receives identical target
and evaluation artifacts. Training receives only the contract, script handle, selection seed
and projected training limits; evaluation seeds/inputs/outputs are not supplied to the learner.
Evaluation runs only after training returns and cannot alter search/stop choices.
Hashes and SQL checks reject full-word overlap. Prefix reuse is expected; this is not a
claim that all word prefixes or transition observations are statistically independent.

Evaluation executes the real original once per pair and reuses its fixed reference traces
across methods/checkpoints. It evaluates serialized learned transition models, not a fresh
oracle call per predicted output. Standalone export is generated and its interpreter is
covered by M3 tests; no extra live twin cost is invented for each offline prediction.
Reference-oracle action/reset costs are reported once per pair, outside training numerators.

## Checkpoints and metrics

Equal original-action **ceilings**: 250,500,1000,2000, 3000-reset cap and 120-second soft wall
limit per training cell. Snapshots contain only the most recent complete hypothesis available
by that physical action count. A hypothesis generated at the exact ceiling may update that
snapshot without a further oracle call. No later model is backdated. No model means an
explicit unsupported region, zero trace/step fidelity; no plausible target output is invented.

Some policies stop a few actions early when no affordable new candidate remains. We record
actual spending and carry forward that already-available model; no padding or fictitious
action count is used. Results compare equal budget ceilings, not a false assertion that every
cell physically consumed exactly every ceiling. Missing/failed runs remain visible.

Primary threshold: first predetermined checkpoint at >=95% exact full-trace fidelity.
Unreached is null/right-censored at the allowed ceiling, never a fabricated success cost.
Resolution is checkpoint-level, not an exact minimal-query threshold. Fidelity is reported at
all ceilings. AULC is the left-constant step integral from (0,0), divided by 2000; the final
endpoint has zero measure. Perfect fidelity first observed at 250 yields AULC 0.875.
No monotonicity or linear interpolation is assumed.

Paired differences report median, range and win/tie/loss counts, with family detail. With
five seeds and repeated workflow structure, no population-level confidence claim is made.
Preregistered performance rule: at least 80% paired AULC wins and a positive median against
**both** native baselines within a family. All families satisfying it supports the broad
hypothesis; only some supports it partially; none means not supported in this pilot.
Fewer than five seeds/three families, incomplete cells or failures makes it inconclusive.

## Interruption and reproduction

Cells run sequentially. Resume preserves completed receipts and their models/SQL records;
it rejects changed manifest/source identities. An interrupted cell restarts in a fresh
numbered attempt with a fresh learner/cache; previous attempts are retained and reported.
No live AALpy observation table is resumed. A hard kill may leave at most an in-flight action
without a committed result; do not treat its aborted-attempt cost as fully known. Final
pilot artifacts disclose any recovered cells; no failed run is silently selected away.

```powershell
bbt benchmark generate --family random --seed 101 --out runs/example-target
bbt benchmark run --manifest benchmarks/manifests/m4-confirmatory.json --out runs/m4
bbt benchmark run --manifest benchmarks/manifests/m4-confirmatory.json --out runs/m4 --resume
bbt benchmark summary --out runs/m4
bbt benchmark audit --out runs/m4
```

All commands are local. Workflow generation requires an explicit `--workflow-source` when
used directly. Never overwrite preserved evidence or publish without authorization.
