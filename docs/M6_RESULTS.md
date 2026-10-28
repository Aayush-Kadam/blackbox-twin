# M6 results — frozen confirmation v1

Engineering verdict: **PASS WITH LIMITATIONS**. The bounded campaign completed and its
physical accounting, independent executable scores, source separation and support evidence
passed audit. This is an engineering result, not universal reconstruction or algorithmic
superiority. M7 readiness: **READY WITH LIMITATIONS**; M7 has not been started.

## Coverage and provenance

The frozen `benchmarks/manifests/m6-v1.json` produced **216 cells / 324 scored points**:
108 finite training runs with two checkpoints, 72 independently budgeted wallet runs,
12 inventory concrete runs and 24 zero-query inventory compatibility rejections.
There are **21 target instances**: three variants each of easy, medium, delayed and rare
finite families; six wallet configurations; three inventory configurations. Rare variant 0
is the exact historical program and delayed depth 5 is a known structure. They remain
regression strata, not untouched programs. Repeated learner seeds are not distinct targets.

Finite runs use three learner seeds; typed runs use two. Target, learner, training-oracle
and evaluation streams are independent and listed in the manifest. The five-seed suggestion
was reduced before confirmation to fit the laptop. Budgets are 250/1000 for A,
1500/3000 for B and 500/1500 for C. Every target and all evaluation inputs were saved
before the first training action. No grammar or training parameter was tuned on confirmation.

There are **3,811 frozen evaluation sequences**, executed **48,972 times** across scored
twins. Finite short/long sequences are supplemented with directed delayed/rare challenges.
Typed sequences separate seen/unseen values and lengths, exhaustive reachable state/value
contexts, and validation cases. Exhaustive contexts intentionally overlap training:
the audit found **1,488 full-word intersections across scored points, all exhaustive**.
There were zero frozen random/challenge full-word intersections. Exhaustive population
scores are diagnostic reconstruction scores, not an untouched holdout estimate.

## Highest-budget fidelity and coverage

Values are medians of target means, averaging learner seeds within each target first.
They are descriptive summaries; small target counts do not support population confidence
intervals. Full numerators, denominators, target ranges, both ceilings and every stratum
are in `evidence/m6-confirmatory-v1/metrics.csv` and `analysis.json`.

| Track/family | Method | Trace fidelity | Output fidelity | Coverage | Conditional accuracy | False-supported rate | Abstention |
|---|---|---:|---:|---:|---:|---:|---:|
| A easy, 1000 | All three | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0 |
| A medium, 1000 | All three | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0 |
| A delayed, 1000 | StatePrefix | .8000 | .9950 | 1.0000 | .9950 | .0050 | 0 |
| A delayed, 1000 | Random W | .8000 | .9953 | 1.0000 | .9953 | .0047 | 0 |
| A delayed, 1000 | Random | .7600 | .9931 | 1.0000 | .9931 | .0069 | 0 |
| A rare, 1000 | All three | .8000 | .9954 | 1.0000 | .9954 | .0046 | 0 |
| B wallet, 3000 | Fixed grid | .8463 | .7973 | .8729 | .9571 | .0429 | .1271 |
| B wallet, 3000 | Legacy adaptive | .9738 | .9107 | .9107 | 1.0000 | 0 | .0893 |
| B wallet, 3000 | Hardened | .9297 | .8903 | .8903 | 1.0000 | 0 | .1097 |
| C inventory, 1500 | Concrete finite | 0 | 0 | 0 | null | null | 1.0000 |
| C inventory, 1500 | Adaptive/hardened | 0 | 0 | 0 | null | null | 1.0000 |

All easy/medium highest-budget models were also equivalent to their known finite evaluator
tables: 54/54 seed/method instances. Delayed equivalence was 2/9 StatePrefix, 3/9 Random W
and 1/9 random; rare equivalence was 0/27. These are bounded finite-product checks only.
High output fidelity conceals missed critical events, so trace fidelity and challenge
results must remain visible. All 12 concrete inventory runs exhausted their budget before
producing a complete hypothesis; the exported fallback refuses everything. This does not
establish that finite inventory learning is impossible with more resources.

Wallet overall metrics were identical at 1500 and 3000 here. Extra ceiling did not translate
into extra fidelity. Overall trace averages are strongly influenced by many short exhaustive
cases, so the long unseen-value stratum is an essential qualification:

| Wallet method, 3000 | Seen short/long trace | Unseen short trace | Unseen long trace | Unseen long coverage |
|---|---:|---:|---:|---:|
| Fixed grid | 1.0000 | .5000 | 0 | .5271 |
| Legacy adaptive | 1.0000 | .9000 | .7000 | .8134 |
| Hardened | 1.0000 | .8500 | .5500 | .6132 |

At 3000, hardened minus adaptive target-mean trace differences had median -.03736,
range [-.08288, 0], wins/ties/losses 0/1/5 over six targets. Hardened minus fixed-grid
coverage had wins/ties/losses 4/0/2. All paired comparisons, including smaller budgets
and finite families, are retained in `summary.json`; there is no universal winner.

## Guard acceptance and support

Guard metrics use every evaluator-reachable observable context, both integer operations
and each integer -8..8. A successful positive acceptance claim requires status=ok;
refusals count as no acceptance claim. These metrics do not measure full error-label
correctness, updates, or arbitrary input-space guard recovery.

At 3000, adaptive acceptance precision was 1 for every wallet run; recall ranged 1/3–1.
Hardened precision was also 1 throughout; recall ranged 1/6–1. Fixed-grid precision was
1/2–1 where it made positive claims (null on two configurations with none); recall ranged
0–1. Exact per-target/per-seed TP/FP/FN/TN and refusal counts are in `analysis.json`.
No positive inventory claim was made, so precision is null and recall is zero where
the evaluator population contains successful transactions.

The 24 hardened scored wallet models contain 1,952 observed cells, 2,650 inferred-supported
cells and 430 ambiguous cells. Every saved observation reconciled to a physical training
row; all 24 models recompiled exactly from their bounded version spaces. Across their
evaluation steps, statuses were 37,652 OBSERVED, 9,254 INFERRED_SUPPORTED, 1,698 AMBIGUOUS
and 8,748 UNSUPPORTED. Zero false-supported outputs were observed, including inferred
predictions. This is bounded empirical evidence, not a universal soundness proof.

Unknown-state cascades and first refusals are recorded per point. Generated twins preserve
refusal after an unknown input until reset; reset starts a fresh evaluation sequence.
The dedicated concrete-wrapper test also distinguishes boolean true from integer 1.

## Query costs, runtime and criterion

| Recorded side | Actions | Resets |
|---|---:|---:|
| Original training | 214,815 | 51,022 |
| Original frozen references | 45,550 | 3,811 |
| Separate twins, including training regressions | 695,272 | 52,914 |

No partial training/reference attempts or unaccounted original queries were found.
Original training plus reference cost is 260,365 actions / 54,833 resets. Pilot,
verification tests and representative reproduction are separate expenses, not hidden
inside the confirmation total. The nine-cell pilot used 5,241 actions / 1,825 resets;
the corrected adaptive budget recheck added 1,500 actions / 499 resets.

Sequential confirmation took 662.22 seconds; summed recorded training wall time was
285.14 seconds. This includes the recorded adapter work and is not a pure CPU estimate.
Reference/scoring and orchestration account for additional campaign time. Peak RSS was
not measured, and no memory-efficiency claim is made.

Statuses: 94 completed, 98 action_budget, 24 model_class_unsupported; zero unexpected
failed cells. The action ceiling is a limit, not a requirement to spend the whole budget.
Physical phase totals reconcile. Cache counters are recorded where available; subsequent
typed probes replay physically. No comparable full typed cache-hit rate is available.

The predeclared criterion is >=95% full-trace fidelity AND >=95% output coverage.
**138/216 cells never reached it**. Finite qualifying counts were StatePrefix 20/36,
Random W 21/36, random 19/36. Wallet counts were fixed-grid 0/24, adaptive 12/24,
hardened 6/24. Inventory was 0/36, including compatibility rejections. First qualifying
recorded ceilings and actual physical costs are in `analysis.json`; crossings are not
interpolated. Repeated seeds/budget runs are not independent program successes.

## Separate performance conclusions

- A, finite-state reconstruction: **PARTIALLY SUPPORTED**. Easy/medium success is strong
  within these small owned families; rare/delayed challenge failures prevent a broad claim.
- B, typed-input generalization: **PARTIALLY SUPPORTED** within the bounded wallet grammar.
  Unseen long-sequence failures and zero inventory reconstruction limit transfer claims.
- C, evidence-aware abstention: **SUPPORTED within the declared bounded wallet class**.
  Measured concrete errors were zero, with a material coverage cost. Inventory refusal is
  honest compatibility handling, not evidence of learned two-counter behavior.
- D, query-efficiency superiority: **NOT SUPPORTED**. Native Random W was competitive,
  adaptive beat hardened on wallet fidelity, and higher budgets did not repair these
  failures. Bounded physical accounting itself is supported. M4's negative custom-ranker
  verdict remains unchanged; that ranker was not rehabilitated or retested as a new claim.

The support matrix, failure analysis and verification documents define remaining limits.
No M7 implementation, release, push, publication, paid service or external target was used.
