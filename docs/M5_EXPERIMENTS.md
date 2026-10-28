# M5 experiments — frozen, local, bounded

Historical M5 measurements. Configuration B is now development evidence for M5.1;
it is not reused as untouched confirmation. Fresh M5.1 comparisons, coverage/accuracy
denominators and limitations are reported separately in `M5_1_VERIFICATION.md`.

Primary data: `evidence/m5-primary/`; audit: `evidence/m5-audit.json`.
Public contract freeze: `evidence/m5-contract-freeze.json`. The owned configuration
manifest is evaluator-only. Development used cap=4/transaction-limit=2; evaluation used
eval-a cap=4/limit=3 and eval-b cap=3/limit=2. These constants were never inference inputs.
They are disclosed here after execution for evaluator interpretation, not novelty claims.

The development run completed before primary evaluation. Method parameters were then
frozen: grid -8,-1,0,1,8; initial StatePrefix seed 5101, one walk/state, length 3;
1,000-action initial phase; shared total ceiling 5,000 actions/1,000 resets/120 s per cell;
at most three 16-probe rounds; guard/update grammar and deterministic ranking in
`M5_MODEL_SPEC.md`. No weights or rules were changed after inspecting primary results.
Four primary cells compare fixed-grid and adaptive methods on two configurations. This
is a narrow engineering evaluation, not a population-level statistical generalization.

`frozen-inputs.json` contains 60 sequences from seed 510051, frozen before any training:
30 use only fixed-grid amounts, 30 use only reserved -7,-5,-3,2,6,7. Lengths are 4–10;
each starts with a transaction. The same cases and original reference outputs serve
both methods in a pair. All reserved values are absent from every training request,
including differential search, minimization, probes and regressions. No frozen full
evaluation word overlaps physical training. Model snapshots precede evaluation references.

Both methods use the same L*/StatePrefix, physical replay cache, fixed-grid context pass,
guard/update fitter, contract and maximum budgets. The adaptive arm additionally searches
for a discrepancy, shrinks it, probes model boundaries, refits and replays regressions.
Spending differs and is reported; this is not an exact-spending query-efficiency claim.
Reference acquisition happens only after both training cells in a pair return. Learner
file-access tests prohibit oracle source, variant manifest and frozen-input reads.
This is architectural separation, not an adversarial operating-system sandbox.

## Executed flagship

1. Read only the public operation schema and open the local oracle.
2. Learn from the fixed grid and discover observable contexts (130 observations in A,
   104 in B). Initial finite L* hits its declared phase ceiling; it is not called converged.
3. Fit revision-000 guarded model and generate revision-000 standalone twin.
4. Differential search tries permitted, unobserved typed values from recorded access paths.
5. In A, `deposit(4)` from reset returns `transaction_limit` in the original while the
   initial twin predicts success/balance 4. In B, the analogous discrepancy is `deposit(3)`.
6. Real M3 sequence minimization and typed value shrinking confirm one-action discrepancies.
   Smaller trial amounts either agree or change target error class; they are not accepted
   as misleading reductions. Complete raw traces and attempts remain in `counterexample.json`.
7. Four recorded guarded-model revisions (including refitting after the final probes)
   produce final revision-004. These are not four independent CE discoveries: each cell
   has **one** discovered CE, with up to three bounded probe rounds.
8. Final independently executed twins replay the minimized discrepancies with agreement.
   All 163 contextual regressions pass in A and all 127 pass in B.
9. Frozen sequences and exhaustive evaluator contexts are executed after final training.

The evaluator exhaustively checks every in-domain integer for both transaction operations
at every reachable balance/frozen pair: 340 points in A, 272 in B. Each case includes
independent reset/access, the tested transaction and a following get_balance to check
state preservation. Another seven invalid-input cases per context check missing, null,
Boolean, float, string, excessive integer and extra fields (70 cases in A, 56 in B).
Evaluator access paths use its known configuration; they never enter training.

## Measured fidelity

| Configuration / method | Seen-value traces | Unseen-value traces | Unseen exact outputs | Exhaustive contextual traces | Validation traces |
|---|---:|---:|---:|---:|---:|
| A fixed grid | 30/30 | 30/30 | 227/227 | 320/340 | 70/70 |
| A adaptive | 30/30 | 30/30 | 227/227 | **340/340** | 70/70 |
| B fixed grid | 30/30 | **29/30** | **226/227** | 252/272 | 56/56 |
| B adaptive | 30/30 | **19/30** | **156/227** | 264/272 | 56/56 |

Seen-value exact outputs are 222/222 in every cell. Exhaustive exact outputs are
1,490/1,530 versus 1,530/1,530 in A and 1,048/1,088 versus 1,074/1,088 in B.
Validation outputs are 315/315 in A and 224/224 in B for both methods.
The random sequence sample alone misses important fixed-grid failures in A; the
exhaustive contextual check is necessary. Better exhaustive coverage does not imply
better unseen-sequence behavior: adaptive B is materially worse on that metric.

| Configuration / method | Acceptance-guard precision | Acceptance-guard recall | Correct class boundaries / target boundaries | Predicted boundaries |
|---|---:|---:|---:|---:|
| A fixed grid | 0.90 | 1.00 | 26/34 | 38 |
| A adaptive | 1.00 | 1.00 | **34/34** | **34** |
| B fixed grid | 0.833333 | 1.00 | 20/26 | 32 |
| B adaptive | 1.00 | **0.60** | 24/26 | 30 |

Guard population is the 340/272 exhaustive contextual transactions, including frozen
and invalid-amount business outcomes. Positive means target status=ok. Unsupported
predictions are non-acceptance, so they reduce recall rather than disappear. Precision
is correct accepted predictions / all accepted predictions; recall is correct accepted
predictions / all target acceptances. Boundary population consists of adjacent integer
pairs at the same prior balance/frozen context and operation where status/error class
changes. Numerical balance-output differences alone are not boundaries. Extra predicted
boundaries remain in the denominator/explicit count; exact boundary-set equality holds
only for adaptive A.

Unsupported output frequencies on unseen sequences: A both 0%; B fixed 1/227 (0.44%),
adaptive 71/227 (31.28%). On exhaustive sequences: A fixed 36/1,530, adaptive 0;
B fixed 36/1,088, adaptive 12/1,088. After an unsupported action the twin retains an
unknown-state marker until reset, so one ambiguous amount can affect several later
outputs. Error-class mistakes without unsupported markers are also counted as failures.

## Physical cost and size

| Configuration / method | Training actions | Resets | Training wall seconds | Observed states | Rules | Final observations | Model JSON bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| A fixed grid | 1,351 | 462 | 3.350 | 10 | 18 | 130 | 168,556 |
| A adaptive | 2,112 | 666 | 7.963 | 10 | 18 | 163 | 193,009 |
| B fixed grid | 1,208 | 436 | 3.852 | 8 | 18 | 104 | 134,819 |
| B adaptive | 1,741 | 593 | 4.324 | 8 | 18 | 127 | 152,886 |

Times are local single runs including recording/fitting and are not statistical speed
comparisons. All training totals are **6,412 actions / 2,157 resets**. Original shared
post-training references cost **4,055 / 858**, separate from learning. Thus original
primary calls including evaluation total **10,467 / 3,015**. Independent twin executions
cost **9,233 / 2,030**, reported separately. No reference calls are moved into training
efficiency metrics. Initial/reset checks, membership, state-cover, differential searches,
shrink trials, final replay and full regression replay are all included in training.

| Adaptive phase | A actions / resets | B actions / resets |
|---|---:|---:|
| Initial state learning and reset validation | 1,000 / 384 | 1,000 / 384 |
| Fixed-grid context completion | 351 / 78 | 208 / 52 |
| Differential search | 5 / 5 | 4 / 4 |
| Counterexample minimization / value trials | 6 / 7 | 5 / 6 |
| Boundary value probes | 106 / 28 | 65 / 19 |
| Counterexample replay | 1 / 1 | 1 / 1 |
| Regression replay | 643 / 163 | 458 / 127 |

Guard discrimination/refitting use recorded data and cost zero additional oracle calls;
their computation is included in wall time. At most 28/19 new contextual boundary probes
were actually needed, below the 48-probe cap. This is not exhaustive training: six of the
17 argument values are withheld entirely. Per-context coverage and every untested region
remain in the model. Development and installed reproduction costs are not pooled into
these primary numerators. Reproduction repeats one adaptive A cell (2,112 / 666) and
checks 470 standalone cases; it does not repeat all four cells.

## Failures and conclusion

The development configuration exposed unresolved behavior at withheld amount 2; the
same weakness appears in B. Amounts 1 and 3 can bracket a boundary without determining
the behavior at 2. Grouping atoms by observed exclusion sets selects one representative
cut; multiple possible cuts or state relations may remain observationally consistent.
The chosen B deposit rule uses a different state relation than the hidden target at
unseen values, and selected response guards can overlap. Adaptive probing cannot resolve
a value it is expressly prohibited from querying without an adequate other identifying
experiment. A smaller observational fit is not a proof of the hidden guard.

No evaluation result was fed back into this method, and no rescue tuning was performed.
The successful A result demonstrates a real bounded state-dependent rule/update capability,
including untrained amount 2. B demonstrates insufficient identification and abstention
limitations. There is **no demonstrated general adaptive-efficiency advantage** or uniform
unseen-value fidelity advantage over the fixed grid. M4's negative planner verdict remains
unchanged. M5 verdict is PASS WITH LIMITATIONS; broader M6 benchmarking should wait for
a separately specified ambiguity/support policy and new untouched configurations.
