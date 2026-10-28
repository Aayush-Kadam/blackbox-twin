# M4 results — performance hypothesis NOT SUPPORTED

M4.1 clarification: unchanged ablation fidelity curves do not mean unchanged experiments.
Coverage removal changes decision lists in 15/15 pairs; suffix removal changes 13/15.
Both scoring toggles are real. Short-word preference after hypothesis-feature saturation
is supported by saved traces; no score or candidate-generation correctness defect was
found. One unrelated snapshot oracle-label defect was repaired with frozen source
preserved. See `M4_1_DIAGNOSIS.md`. Historical numbers and verdict below remain unchanged.

Primary evidence: `evidence/m4-confirmatory/summary.json`, `results.csv` and per-cell
`result.json`/SQLite records. Protocol: `benchmarks/manifests/m4-confirmatory.json` and
`M4_EXPERIMENT_PROTOCOL.md`. The scoring configuration was not tuned on these results.

## Coverage and methodology

Three families, five paired target/selection seeds each, eight methods: **120 completed
training cells and 480 evaluated checkpoints**. The 15 paired configurations contain
**10 distinct oracle programs**: five random reachable 4–6-state machines, four delayed
threshold variants (4,5,6,3,4) and one order workflow reused across five selection seeds.
Generation seeds 201–205, selection seeds 100201–100205, evaluation seeds 200201–200205.

Each pair has the same 80 frozen words (lengths 24–32) for every method/checkpoint.
Original references are queried once per pair, outside all training numerators. Native
baselines are installed AALpy RandomWMethodEqOracle and StatePrefixEqOracle with a common
BBT observed-prefix replay cache, not an exclusive cache available only to the proposal.
All methods use identical L*, RS processing, adapter, physical limits and recording policy.

The original 101–105 block also completed 120 cells and gave a negative result. Review
noticed coupled generation/selection seed labels. Its artifacts, negative summary, audit
and frozen source snapshot remain at `evidence/m4-pilot/`. The confirmatory block uses
fresh targets, selection seeds and held-out inputs. Only seed separation changed; no
weights, baseline strength, families, budgets or metric rules were retuned. The original
audit was performed against its then-frozen source; current resume guards correctly reject
mixing amended code with that old run. Neither block is silently discarded or pooled to
inflate independent coverage.

## Comparison

All methods receive action ceilings **250,500,1000,2000**. Threshold is the first fixed
checkpoint with >=95% complete-trace agreement. The threshold median below is conditional
on reaching it; unreached cases remain null in the raw data, not assigned a success cost.
The value 750 is the arithmetic median of discrete qualifying checkpoints, not an observed
exact 750-action threshold. Conditional threshold medians alone cannot rank methods fairly
when different cases are censored; always retain the reach counts. AULC uses the
preregistered left-constant integral from (0,0).

| Strategy | Reached 95% | Median qualifying ceiling among reached | Median AULC | Median resets at run end | Sum training wall, 15 cells (s) |
|---|---:|---:|---:|---:|---:|
| Uniform-length random | 14/15 | 750 | 0.759375 | 262 | 13.353 |
| Breadth-first | 13/15 | 1000 | 0.734375 | 421 | 15.279 |
| AALpy Random W | **15/15** | 1000 | **0.770313** | 234 | **12.186** |
| AALpy StatePrefix | **15/15** | 1000 | **0.770313** | **195** | **11.256** |
| Cost-aware proposal | 13/15 | 1000 | 0.710938 | 408 | 31.656 |
| Without cost ranking | 14/15 | 1000 | 0.729688 | 259 | 26.149 |
| Without coverage ranking | 13/15 | 1000 | 0.710938 | 409 | 33.360 |
| Without separator contribution | 13/15 | 1000 | 0.710938 | 411 | 29.816 |

| Strategy | Median exact-trace fidelity at 250 | 500 | 1000 | 2000 |
|---|---:|---:|---:|---:|
| Random | 61.25% | 91.25% | 100% | 100% |
| Breadth-first | 61.25% | 81.25% | 100% | 100% |
| Random W | 61.25% | 91.25% | 100% | 100% |
| StatePrefix | 61.25% | 91.25% | 100% | 100% |
| Cost-aware | 61.25% | 81.25% | 100% | 100% |
| No cost ranking | 61.25% | 62.50% | 100% | 100% |
| No coverage ranking | 61.25% | 81.25% | 100% | 100% |
| No separator contribution | 61.25% | 81.25% | 100% | 100% |

These medians conceal important failures; they do **not** mean every model achieves 100%.
The full proposal remained at **65/80 traces (81.25%)** on delayed seed 202 and **73/80
(91.25%)** on seed 203 at every checkpoint. Both native methods reached 100% by ceiling
1000 on seed 202, and by 2000 on seed 203. The full method's end fidelity
range was 81.25–100%; native baselines were 100% on all 15 final checkpoints.

## Paired evidence and variation

For cost-aware AULC minus baseline, across the same 15 paired configurations:

| Baseline | Full proposal wins / ties / losses | Median difference | Difference range |
|---|---:|---:|---:|
| Random | 0 / 12 / 3 | 0 | [-0.290625, 0] |
| Breadth-first | 0 / 13 / 2 | 0 | [-0.193750, 0] |
| Random W | **0 / 12 / 3** | 0 | [-0.281250, 0] |
| StatePrefix | **0 / 11 / 4** | 0 | [-0.290625, 0] |

The delayed-family median AULC difference against **both** native methods was **-0.09375**;
random and workflow medians were zero. No family meets the preregistered improvement rule.
The difference between two pooled method medians is not the median paired difference;
most paired cases tie, while losses concentrate in the delayed family.
The first pilot likewise had zero AULC wins against either native baseline. This supports
the narrow negative conclusion that this implementation has no demonstrated query-efficiency
advantage on the measured pilot. It does not prove that model-guided planning can never help.
With five seeds and repeated target structure, ranges/win counts are descriptive pilot
variation, not population-level confidence intervals or statistical significance claims.

## Ablations and failure analysis

- Removing coverage ranking produced **identical complete checkpoint fidelity curves**
  in all 15 pairs. Removing separators did the same. There is no measured fidelity value
  for these added components on this suite. These ablations remove ranking contributions;
  some feature computation remains, so their wall times do not isolate pure extraction cost.
- Removing cost ranking improved AULC in two pairs and worsened one (12 ties), and reached
  the threshold in 14 rather than 13 cases. Its aggregate median AULC was higher, but its
  500-action median was worse. The cost component offers no reliable positive contribution.
- The closed L* table already covers learned transitions. Coverage of a merged one-state
  hypothesis does not establish coverage of hidden control states. Favoring short novel
  contexts can postpone longer distinguishing behavior; these observations and the score
  definition suggest why the proposal fails on deep delayed variants. They are not a proof
  of a universal causal explanation.
- Post-hoc **evaluator diagnostic probes**, not planner discoveries, executed five advances
  plus commit for seed 202 and six advances plus commit for seed 203. Originals accepted;
  final independently executed twins denied. Their SQL and comparison records are in
  `evidence/m4-failure-probes/`. The 13 original actions/2 resets were diagnostic costs,
  separate from the frozen benchmark, and were never fed back into training.

All policies have more tied/easy cases than difficult delayed distinctions. Random FSM
outputs and workflow status/error outputs often let membership learning identify the model
before exploration strategies differ. This limits suite discrimination and is not evidence
that a complex heuristic is useful. A simpler baseline achieved equal or better fidelity.

## Costs, overhead and unsuccessful thresholds

The primary block executed **239,861 original training actions and 42,066 resets** across
120 cells, plus **33,780 evaluator reference actions and 1,200 resets** shared across all
methods/checkpoints. Thus the full primary block cost **273,641 original actions / 43,266
resets including evaluation**. Do not label that combined total training cost. The sum of
recorded per-cell training wall time was **173.054 seconds**; target generation, reference
generation and offline scoring are outside that sum. Individual timings are local measured
runs in fixed method order, not controlled cross-machine performance estimates.

The proposal spent 29,967 physical actions across its 15 runs, versus exactly 30,000 for
each native baseline. **62/120** cells stopped 1–5 actions below their final ceiling
(minimum 1995); these are disclosed policy stops, not 62 infrastructure failures. All
250/500/1000 checkpoints had been physically reached. Top-ceiling comparisons are explicitly
budget-ceiling comparisons using the model already available at actual spending. No padding
or fictitious execution is used, and the few unspent actions are not advertised as a gain.

Total search actions divided by confirmed counterexamples (a descriptive full-budget ratio,
not time to first discovery) were: random 22,413/8; BFS 23,614/6; Random W 22,186/7;
StatePrefix 22,080/8; full proposal 23,976/5. All membership and refinement interactions are
additionally charged to the training totals. M3-style separate shrinking/regression phases
are absent for **every** method in this selection-isolation track, so their costs are zero,
not hidden in an excluded category. Real M3 integration is verified separately by tests.

The proposal's search/bookkeeping overhead total was **18.158 s**, versus **0.259 s** Random
W and **0.221 s** StatePrefix. This timer subtracts timed pre/step adapter work; it can include
post/recording bookkeeping and is not a pure CPU profiler. Pure proposed candidate-scoring
time is also stored per cell. Holistic training wall time was about 2.6x/2.8x those native
totals respectively. No oracle savings justify that observed overhead.

Development recording profiling ran identical 200 actions/40 resets: default recording
0.904 s, uniformly applied WAL mode 0.164 s. This is a storage configuration observation,
not an algorithmic planner benefit. Profile evidence: `evidence/m4-profile/profile.json`.

## Reproduction and next decision

Six cells (third frozen seed 203, all three families, full proposal and Random W) reproduced
from a non-editable installation. Physical action/reset counts, counterexamples, every
checkpoint state count and fidelity matched exactly. See `evidence/m4-reproduction/summary.json`.
The entire 120-cell matrix was **not** repeated from a second installation; do not expand
that claim. Completed-cell resume was executed and left the result matrix unchanged.

Recommendation: **reconsider the current proposed strategy**, retain strong native baselines,
and investigate a better evidence-backed objective before claiming query efficiency or
expanding into M5. Do not tune on the now-observed held-out sets. A new comparison requires
new development/evaluation separation. No further milestone was implemented automatically.
