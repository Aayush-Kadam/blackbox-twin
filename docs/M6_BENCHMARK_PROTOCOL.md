# M6 protocol — version 1, bounded consumer-laptop campaign

**Frozen confirmatory v1:** `benchmarks/manifests/m6-v1.json` exists with package/resource
hashes and independent seed lists. The nine-cell development pilot and targeted budget
status recheck completed before freezing. The owner explicitly authorized normal reviewed
creation of `m6_train.py`, and review accepted it. Confirmation completed all 216 cells /
324 scored points and passed audits. The design below remains the frozen protocol;
actual results and deviations are in `M6_RESULTS.md` and `M6_VERIFICATION.md`.

This document and `benchmarks/manifests/m6-v1.json` define the confirmatory campaign.
The machine manifest, all package source, owned fixture template and historical rare
fixture are fingerprinted after the small pilot and before confirmatory execution.
Development data never enter confirmatory learning or selection. No parameter tuning
after inspecting confirmation. A changed source/protocol requires a separately identified
run; completed cells and failed attempts are preserved.

## Tracks and coverage

- A: easy reachable random Mealy machines (3–5 states/2–3 inputs/2 outputs), medium
  machines (8–10 states/3–4 inputs/4 outputs), delayed threshold machines (depths 5,7,9),
  and rare ordered paths (lengths 7,9,11). Three variants per family. The exact historical
  `abacaba,c` program is retained byte-for-byte as a regression stratum and is not an
  untouched target. Delayed depth 5 is also a known-structure regression; depths 7/9
  are new. Random machines use fresh generation seeds; delayed/rare graphs are fixed
  configurations and their unused RNG labels do not create independent programs.
- B: six new wallet configurations span caps 1,2,3,4, transaction limits, a minimum
  amount of 1 or 2, frozen transactions enabled/disabled and a keep/subtract withdrawal
  update. Public integer/balance bounds stay -8..8 / 0..4. Hidden configuration never
  reaches the learner. These changes remain within the already declared guard/update
  grammar; no confirmatory grammar enlargement is allowed.
- C: three inventory-reservation programs with caps 2,3,4 and bounded available/reserved
  counters. Public contract: stock(quantity), reserve(quantity), release(), consume(),
  inspect(), integer quantity -8..8. Reset stock/reservations to zero. Outputs status,
  available and reserved plus error on failure. Unknown operations, missing/null/bool/
  float/string/extra fields and out-of-domain values have explicit state-preserving
  validation errors. Business rules are evaluator-owned. Two-counter guarded inference
  is unsupported; record this compatibility rejection before expensive queries.
  A generic finite-concrete baseline is evaluated without pretending it generalizes
  numeric arguments. Its unseen-input refusal poisons state until reset.

Mealy transition functions are total; graph connectivity varies by construction. This
is not a sparse partial-transition experiment. Unreachable hidden states are not counted
as successful reconstruction. Inventory uses a separately implemented evaluator; wallet
references also cross-check an independent transition implementation after training.

## Sizes, seeds and costs

Track A: 12 targets x 3 learner seeds x 3 strategies = 108 training runs, with 250/1000
physical-action checkpoints from each single run. Strategies: native StatePrefix,
native Random W, uniform random. Track B: six targets x two learner seeds x three methods
x independent 1500/3000 ceilings = 72 runs. Methods: fixed grid, legacy adaptive,
evidence-aware hardened. Track C: three targets x two learner seeds x three methods
x 500/1500 ceilings = 36 cells; 24 are explicit guarded-model compatibility rejections
with zero training calls, 12 are concrete finite runs. Total 216 cells, 21 distinct
target instances including one historical regression. Repeated seeds/checkpoints are
not independent programs. The suggested five-seed goal is reduced to three/two to cap
training at 282,000 original actions and keep sequential execution practical.

Target, learner, training-stream and evaluation seeds occupy independent ranges. Native
oracle random streams are isolated from the learner's global RNG. No numeric offset
couples a target seed to its paired learning/evaluation choices. The manifest records
the actual lists. Typed initial L*/StatePrefix remains common (one walk/state, tail 3,
initial phase ceiling min(1000,total)); equivalent defaults remain unchanged for M5.
Per cell resets <=3000, time <=120 s; max training sequence 100. One worker, no concurrent
heavy suites. No paid service, external target or M7 implementation.

## Frozen evaluation

All inputs are generated and saved before any campaign training. Each A target has 40
random short/long sequences (16–24 and 48–64) plus 10 evaluator-owned delayed/rare challenge
sequences where applicable, padded to long words. Challenges are never passed to training.
Typed targets have 20 seen-value and 20 unseen-value sequences in short/long strata,
with unseen values -7,-5,-3,3,6,7 and training grid -8,-1,0,1,8. All exploratory, shrink
and regression calls exclude reserved values. Wallets also receive exhaustive one-step
state/value cases from evaluator-reachable contexts, and invalid-input/state-preservation
cases. Inventory has independent adversarial and invalid-sequence cases. Evaluator costs
are separate and references shared across methods/seeds/budgets for each exact target.
No reference outputs are acquired until that target's training cells finish.

Standalone processes execute every scored checkpoint. A finite-product evaluator additionally
checks the known finite Mealy table, but no arbitrary-program equivalence is inferred.
Full-word overlap counts are audited; any accidental overlap is reported, not silently
regenerated. Reserved-value sequences cannot be training words. Source/contract/inputs
are fingerprinted and original truth is reconciled to physical events.

## Metrics, criteria and analysis

Primary: exact full-trace and individual-output match numerators/denominators, concrete
prediction coverage, conditional concrete accuracy, false-supported rate and abstention.
Refusals do not count as reconstruction matches. Empty conditional denominators are null.
Primary cost criterion: >=95% exact traces AND >=95% output coverage on the declared
evaluation set. Report the first recorded ceiling satisfying both or null if unreached;
these are discrete checkpoints, not interpolated crossing costs. Compatibility rejection
is not an efficiency success. Failed/incomplete runs remain in denominators.

Secondary: resets, phase costs, wall time, cache counters where exposed, model size,
counterexamples/shrink/regression statistics where applicable, support-region sizes,
unknown-state cascades, reset recovery, guard acceptance precision/recall on explicitly
defined state/transaction populations. Peak RSS is not collected: no reliable comparable
cross-process sampler is configured; do not claim memory efficiency. Planning/fitting CPU
is included in wall time; only exposed search timers are separately labelled, not pure CPU.

Average learner seeds within each target before family medians/spread and paired method
differences. Report target-level ranges and wins/ties/losses, failures and unreached cases.
Do not count checkpoints or repeated seeds as independent programs. With only 3 variants
per finite family and six wallets, use descriptive statistics, no population confidence
or significance claims. Report seen/unseen, length and adversarial strata separately.

## Reliability and stages

First run the existing test baseline and a <=5750-action development pilot (one easy,
one distinct wallet and one inventory configuration). Preserve pilot failures; do not
call pilot data confirmatory. Freeze v1 only after runner/accounting tests and cost review.
Completed training receipts/checkpoints survive interruption. Resume verifies source,
manifest and artifact hashes, reuses completed cells, and restarts interrupted attempts
in new folders. Live AALpy table continuation is not claimed. Partial reference attempts
are preserved and charged when restarted. Corrupt checkpoints fail integrity checks.
Unexpected failures are recorded distinctly from action-budget censoring/model-class
limitations. No completed expensive cell is rerun merely for nicer results.

At completion audit accounting, source separation, all metric denominators, failures,
standalone replay and representative non-editable reproduction in each executable class.
Preserve M4's negative ranker verdict. Engineering completion and performance conclusions
are separate, and no M7 work starts automatically.
