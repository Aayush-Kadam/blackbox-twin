# M4.1 adversarial diagnosis — 2026-10-27

**M4.1 — COMPLETE WITH LIMITATIONS. Outcome B: legitimate algorithmic weakness.**
The evidence supports retiring the custom ranker from the recommended path and selecting
native AALpy StatePrefix. No revised ranker has demonstrated improvement. The historical
M4 performance verdict remains **NOT SUPPORTED**. M5 is ready for scoped design/implementation
approval, subject to the gates in `M5_READINESS.md`; it has not been implemented.

## Evidence and preservation

Read-only analysis covered saved M4 decisions, physical experiments, timings, phase costs,
models, manifests and results. `evidence/m4-1/historical.json` contains per-cell summaries;
`forensic-summary.json` compares ablation decisions, checks diagnostic costs, and records
independent post-training finite-product comparisons for development fixtures.
The existing staged tree remains `9d804578899a21849533231252b1a2fbb7e23059`.
No commits, pushes, releases or modifications to historical observations/scores occurred.

Before changing model metadata, the frozen M4 core was copied to
`evidence/m4-confirmatory/source-snapshot/blackbox_twin/`. The audit passed before the
change and again with this snapshot: `prechange-m4-audit.json`, `frozen-source-m4-audit.json`.
These confirm 120 cells, 480 recomputed scores, 239,861 training actions / 42,066 resets,
and separate shared evaluator costs of 33,780 / 1,200. The snapshot preserves the hashed
training/metric sources; ancillary CLI files were copied after the new CLI default was
prepared. Benchmark execution does not use that CLI learning default.
Current-source M4 audit/resume rejection after the metadata repair is intentional.
Never rewrite the old source hash to accommodate new code.

## Findings against the six hypotheses

| Hypothesis | Finding | Evidence and limits |
|---|---|---|
| Short-sequence bias | Confirmed mechanism; substantial explanation for delayed failures | On delayed 202 and 203, full custom median physical search length was 5; StatePrefix was 16 and 17. Custom selected lengths were 3–6, so the seven-action shortest probe for 203 was never selected. The six-action probe for 202 was not selected despite other length-six words. |
| Coverage ineffective | Correctly implemented, active but rapidly saturated and insufficient | Full method had nonzero selected coverage in 1,397/4,974 decisions. This combines learned edges and three-input contexts; it is not hidden-target coverage. Removing it changed decision lists in all 15 pairs while leaving checkpoint fidelity curves identical. |
| Separator ineffective | Active on multi-state hypotheses; unavailable on merged one-state failures | Nonzero separator bonus in 3,603/4,974 full decisions. Removing it changed decision lists in 13/15 pairs; only failed delayed 202/203 had identical lists. Their learned one-state hypotheses have no state pairs to separate. |
| Restrictive pool | Real general limitation, not absence of the shortest delayed probes | All repeated-symbol-plus-last-symbol probes of length 3–12 are generated, including advance^5,commit and advance^6,commit. They are length-valid and unobserved in the failed cases. No pool pruning defect was found for these words. Arbitrary ordered paths depend on only 64 random proposals per selection; access+tail and access+separator candidates over length 12 are discarded. |
| Native exploration | Confirmed material differences | Native StatePrefix explores from each learned state's access path, longest access first by default, followed by 12 random inputs. Custom has a total-word cap of 12 and repeatedly starts short novel words. Native has fewer resets and longer paths per reset; both pay full physical replay. State-guided walks are established AALpy behavior, not a BBT contribution. |
| Planning overhead | Confirmed redundant work | Every selection traverses all historical prefixes under the current model, recomputes candidate features, and computes separators both before ranking and within generation. This work did not improve the measured curves. |

The delayed ranker does not look ahead to unknown states. Once its merged hypothesis has
covered every learned transition and three-input context, all remaining such probes have
coverage zero and there are no separators. Scores then reduce to `1/(length+1)`.
For example, development delayed-302 decision 51 chooses a length-four word at 0.2,
while length-twelve alternatives score 1/13. The required six-action probe is present in
every generated structural pool, but its zero-coverage score is only 1/7. Many short
unqueried words remain. The exact lexical tie-break additionally chooses the greatest
symbol tuple at equal score/length; this is deterministic, not a discovery guarantee.

In the depth-five development fixture there were 2,248 nonzero-coverage candidate instances
over 121 logged proposals, yet only lengths 3–5 were selected. Coverage is neither
constant nor globally inactive. Once saturated it cannot discriminate hidden progress.
The random development fixture had 8,741 candidate instances with a separator bonus;
separator generation/arrival/scoring are demonstrably active outside one-state models.
Observed repeated candidates across proposals are counted as instances, not unique words.

This explains a concrete selection mechanism, not a universal causal attribution of every
loss. Coarse checkpoints can conceal different discovery times. Candidate-pool breadth,
random diversity and the cost penalty were not independently randomized in a factorial
study. No claim is made that all separator methods or all cost-aware planning fail.

## Ablation integrity and defects

Controlled tests provide candidates with unequal coverage, separator contributions and
costs. Disabling each term changes the score/order when mathematically expected. Tests
also check lexical ties and affordability rejection. No inactive toggle, wrong score
formula or missing repeated-probe generation bug was found.

The suffix ablation intentionally removes both explicit suffix-generated candidates and
the bonus; it is a component ablation, not a pure coefficient intervention. It still
computes separators within `candidates`, which is wasted computation, not an enabled bonus.
The coverage ablation still extracts features. Old wall-time differences therefore do
not isolate feature extraction. No historical results were replaced.

One **metadata defect** was found and repaired: `learning.py` hardcoded
`eq_oracle=RandomWMethodEqOracle` for every delegated snapshot. It now records the
delegate's method or actual class. Historical benchmark method fields, routing and
scores were correct; this defect does not explain the performance gap. Old snapshots
remain untouched and must be interpreted using their accompanying method records.
No algorithmic repair, replacement ranker, weight search, committee or solver was added.

## Timing diagnosis

Two uninstrumented development cells were profiled separately from diagnostic logging.
On delayed depth five / 500-action ceiling, custom used 497 actions and StatePrefix 500.
Local profiled wall times were 1.874 s and 0.660 s. Instrumentation/profiling changes timing;
these are diagnostic single runs, not a new runtime benchmark.

| Custom stage | Profile evidence |
|---|---|
| Model traversal | `features`: 23,387 calls, 0.282 s exclusive / 0.458 s cumulative |
| History aggregation, score construction and ranking | `propose`: 121 calls, 0.159 s exclusive / 1.138 s cumulative |
| Candidate generation | `candidates`: 0.064 s exclusive / 0.402 s cumulative; random-tail generator adds 0.038 s exclusive |
| Deduplication | `dict.fromkeys`: 121 calls, 0.009 s exclusive / 0.024 s cumulative, included in candidate-generation totals |
| Oracle/recording path | `_call`: 628 calls, 0.593 s cumulative; includes transport and recording, not pure target CPU |
| Refinement | No custom counterexample, so no refinement in this profiled cell; phase costs distinguish membership from equivalence search |

Cumulative times overlap and must not be added. Scoring and historical-set aggregation
share the `propose` frame and are not separately isolated. Actual oracle elapsed time is
recorded separately in every training receipt and the historical SQL event summaries;
subprocess CPU time cannot be isolated from request elapsed time. This remaining profiling
limit does not prevent the default decision. Neither repeated feature extraction nor
extra pool scoring produced additional counterexamples in these delayed development cells.

## Fairness and near-ceiling stops

The frozen audit and code review confirm common L*, RS processing, reset validation,
isolated per-cell processes/DBs/caches, domain-separated generation/selection/evaluation
seeds, shared paired references, no full-word overlap, and post-training scoring only.
Membership and counterexample search/refinement are charged in every method. There are
no excluded shrinking/regression phases in this comparative track. The common cache
replays the entire physical prefix for a novel suffix; cached logical steps are not
misreported as new oracle actions. Checkpoints retain only hypotheses available at the
ceiling, including incomplete refinement and absent models.

62/120 cells stop 1–5 actions below 2,000. Custom policies reject a complete candidate
whose replay length exceeds the remaining budget and stop if the sampled eligible pool
is empty. Native policies can be interrupted partway through a word by per-action limits.
Neither can overrun; this is a conservative atomic candidate policy, not lost physical
calls. It does not prove there is no affordable word outside the sampled pool. Thus the
comparison is equal ceilings, not universally equal exact spending. The maximum 0.25%
tail cannot explain models already deficient at 250, 500 and 1,000. No padding or
negligible-tail optimization was performed; native/custom length policies remain a
declared difference in the tested strategies.

## Bounded development results

Protocol saved before the cells in `evidence/m4-1/development-protocol.json`.
Fresh development target seeds 301/302, selection 400301/400302, 500-action limits.
No held-out benchmark was rerun or used in training; no weights were changed.
Four fixtures cover output-rich short identification, delayed depths four/five, and the
rare ordered path `abacaba,c` with seven-step access. The latter two mechanisms share
one fixture; it does not independently isolate access cost from rarity.

| Fixture | Custom full actions / resets; CE count | StatePrefix actions / resets; CE count | Final-model evaluator result |
|---|---|---|---|
| Random 301 | 499 / 126; 0 | 500 / 73; 0 | Both agree on the entire finite product |
| Delayed 301, depth four | 498 / 132; 0 | 500 / 85; 1 | Custom fails; StatePrefix agrees on finite product |
| Delayed 302, depth five | 497 / 131; 0 | 500 / 79; 1 | Both final models still fail; native refinement incomplete at ceiling |
| Rare ordered access | 498 / 132; 0 | 500 / 51; 0 | Both fail on `abacaba,c` |

Three development ablations on delayed 302: no-cost 500/64, no-coverage 496/132,
no-suffix 497/131; none finds a CE and all retain the deficient model. No-cost selects
lengths up to 12 but is not a demonstrated repair. Exact finite-product checks were
performed by the independent evaluator after training, using the owned fixture tables;
they do not grant equivalence for arbitrary targets or transfer hidden state to learners.

Eleven diagnostic cells consumed **5,485 actions**, two uninstrumented profile cells
**997**, combined **6,482 / 1,346 resets**, below the declared 6,500-action diagnostic
cap. One instrumentation constructor indexing error aborted before learning after reset
validation: **6 / 2**, preserved at `evidence/m4-1-instrumentation-abort/`. It was fixed,
and the fresh diagnostic run retained all failures and successes. Read-only path-label
postprocessing was corrected without rerunning physical cells.
CLI verification separately spent **1,500 / 148** (honest budget exhaustion/checkpoint,
no exported twin) and **282 / 57** (`--walks 2`, completed sampled search and twin).
All non-test new original calls total **8,270 / 1,553**. Automated test calls are separate.

## Default, diagnostics and verification

`bbt learn` now defaults to `--strategy aalpy-state-prefix`, 25 walks/state and 12 tail
inputs, with common replay caching and physical limits. All eight M4 choices remain
explicit CLI options. The custom ranker is experimental and currently underperforming.
The CLI native oracle conducts a finite sampled search; the comparative benchmark
repeats native batches toward a budget. This stopping difference is explicit: a CLI
completion is not a claim of exhaustively spending the budget or proving equivalence.
Low-level `learn()` without a factory and M3 continuation defaults retain their historical
Random W behavior for reproducibility; use `learning_options()` for the recommended
application policy. No benchmark method definition changed.

Optional `DiagnosticPlanner` leaves the original scorer untouched; bounded records include
generated/unique/eligible counts, length histograms, feature contributions, top 12 scores,
longest candidate, selected word/reasons, estimated and actual costs, and CE/model-change
fields. Model-change is null when no subsequent hypothesis was observed; it is not
assumed true on discovery. The recorded custom cells had no CE. No hidden target state
is logged. Diagnostic timings are excluded from the uninstrumented profiles. Logging
was not used in the historical confirmatory study.

**88 tests passed, zero failed, 162.61 s** (`evidence/m4-1/pytest.txt`), including all
unchanged M0–M4 tests and six focused M4.1 tests for scores/toggles/ranking/ties/budgets,
bounded choice-preserving diagnostics and default/retained strategies. Ruff check and
format check pass; no static type checker is configured. CLI smoke artifacts verify
correct `StatePrefixEqOracle` provenance and standalone export on finite completion.
Windows pipe/cleanup/timeout fixes and assertions remain intact.

Commands from the enclosing workspace (set TEMP/TMP to `work` for tests):

```powershell
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/diagnose_m4_1.py --out <new-empty-output>
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m4_1.py
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m4-1-full-tests
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
```

For frozen M4 audit, set PYTHONPATH to the absolute
`evidence/m4-confirmatory/source-snapshot` directory, then import
`blackbox_twin.benchmark_audit.audit_suite` and call it on the primary evidence directory.
Clear PYTHONPATH afterwards. This actual audit result is saved; normal new-source audit
is not falsely claimed to match frozen training code.

The remaining uncertainties are generalization beyond these families, the individual
causal weight of pool diversity versus scoring, the exact benefit of alternative
separator constructions, and pure scoring versus aggregation overhead. None justifies
another optimization campaign. Stop ranker development here. Next action: review the
bounded M5 design and acceptance gates, then implement only when M5 is authorized.
