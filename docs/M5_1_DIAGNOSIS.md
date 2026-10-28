# M5.1 Configuration B autopsy

Historical M5 results are unchanged. All original B unseen data are now **development
regressions**, not untouched confirmation for the modified method. Fresh results are
separately frozen at `evidence/m5-1-fresh/`.

## Complete inventory

`evidence/m5-1-autopsy/inventory.json` records all 30 unseen sequences, every action,
target output, independently executed original twin output, inferred state before/after,
matching guard/update rules, supporting observation indices, observed/generalized/refusal
classification, first divergence, and original model reference. Summary:

- 19 exact traces, 11 failures, reproducing the historical M5 report.
- All 11 first failures are `deposit(2)` in active balance-zero state.
- Every first-failure state is represented and agrees with the target's prior output.
- All 11 first failures arise from **two overlapping selected response guards**, not
  from a failed reset, unknown prior state, first-step numeric update, or normalization.
- The target accepts and returns balance 2. The original twin refuses, then marks its
  state unknown, producing further refusals. These cascades explain the 71 unsupported
  outputs in the unseen sample. Unknown-state propagation was already defensible; the
  overlapping guards and insufficiently localized cut were the upstream problem.

This classifies the measured first failures; it does not assert every B failure has that
cause. The exhaustive population contains two **incorrect concrete** predictions that
the 30 unseen sequences did not expose. `concrete-error-inventory.json` retains them:
withdraw(2) at active balances 0 and 1 should return `insufficient`, while the old twin
returns `transaction_limit`. Their numerical state preservation happens to agree, but
the error class does not. No arithmetic defect is needed to explain these cases.

The old accepted-deposit rule includes `amount <= 2`, while the selected transaction-limit
rule includes `amount >= 2`. Both fit observed amount 1 and amount 3, yet their chosen
cut overlaps at untested amount 2. M5's atom deduplication retained one cut for an
observed exclusion set, its candidate pool was capped, and it selected a regularized
representative. Distinct behaviors at untested values were lost. Some fitted state
relations also differ from the actual target relation; the autopsy does not uniquely
attribute every exhaustive failure between cut choice and state-feature choice.

The stored evidence supports neither an evaluator defect nor a collapsed global-state
rule as the primary unseen-sample explanation. The selected rules already use state;
their existence did not establish sufficient evidence for the untested applicability region.

## Why an ambiguity can be unavoidable

For the original B training split, amount 2 was prohibited. Consider the owned fixture
with cap 3 and transaction limit 1 versus cap 3 and limit 2. On every permitted integer
amount other than 2, both configurations behave identically: nonpositive values have
the same error, amount 1 has the same update and state-dependent rejection, and amounts
3–8 exceed both transaction limits. Control operations and reset are also identical.
By induction, arbitrary sequences of permitted actions cannot distinguish these two
configurations. Merely changing the ranking of those probes cannot identify amount 2.
This evaluator-side argument was not provided as an inference rule to the learner.

The appropriate response is a recorded ambiguity, not a convenient threshold. The new
policy preserves all distinct bounded guard functions and can gather information only
where a distinguishing value is permitted. It does not consult target source at runtime.

## Replayed development regressions

`scripts/regress_m5_1.py` independently reexecutes the original and the new policy twin
on the 30 unseen plus 272 exhaustive historical cases. The new target outputs equal the
saved historical references. `policy-regressions/regressions.json` preserves the original
target, incorrect/refused original prediction, original model and new outcome for every
case. No old failure is deleted.

| Historical population | Correct new predictions | Explicit abstentions | Incorrect concrete predictions |
|---|---:|---:|---:|
| Unseen sequences | 19 | 11 | 0 |
| Exhaustive contextual sequences | 264 | 8 | 0 |

All 19 historical failing cases remain visible as abstentions, **not repaired matches**.
No infrastructure failure occurred in these replays. The artifact's categories distinguish
correct prediction, incorrect prediction and explicit abstention; transport failures
propagate as infrastructure errors rather than becoming matches.

Unseen fidelity stays 19/30 traces and 156/227 outputs. Exhaustive fidelity becomes
1,072/1,088 outputs, compared with the original 1,074/1,088. Concrete prediction coverage
drops from 1,076/1,088 to 1,072/1,088; conditional concrete accuracy improves from
1,074/1,076 to 1,072/1,072. The two false concrete error classifications are now refusals,
and their following actions also refuse because state is unknown. This is a safety and
evidence-status correction with an explicit coverage cost, not improved raw fidelity.

## Development decisions and remaining uncertainties

A small prototype first converted an already completed adaptive seed; it found no
remaining permitted ambiguity probes. Its 2,855-action receipt is preserved at
`evidence/m5-1-development-adaptive-seed/`. The final architecture instead shares the
same fixed-grid StatePrefix seed with the baseline, then resolves actual version-space
ambiguities. A four-probe development cap executed real experiments and preserved 108/108
regressions (1,631 actions); artifacts are at `m5-1-development-fixed-seed/`. This is an
architectural component separation, not a parameter sweep. No method or weights changed
after the fresh evaluation.

During new-model development, a tuple/list JSON round-trip defect was found by a focused
test and fixed before freezing: domain pairs are now serialized as lists. It did not
alter historical M5 results. No M5 arithmetic implementation bug or hidden source leakage
was found. The old model-class and state-sufficiency assumptions remain restrictions;
future targets could violate them even when a current candidate-space consensus exists.
M5.1 does not prove that arbitrary hidden software belongs to the supported grammar.
