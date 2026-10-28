# M6 interrupted-session recovery — 2026-10-27

**Later recovery update:** the owner explicitly authorized resubmitting the same creation
through normal review. Review accepted `m6_train.py`; no bypass was used. The bounded
adapters and runner were then tested. A nine-cell pilot completed, exposing a budget-status
defect that was fixed and rechecked before freezing confirmatory v1. The text below
preserves the original recovery inspection and is historical, not the current blocker.

Current phase: **M6.0 preparation, not frozen or complete**. No pilot, confirmatory
training cell, benchmark reference acquisition or M6 result was found. Test-run files
under `work/m6-*` are verification artifacts, not benchmark cells.

## Retained implementation

- `docs/M6_BENCHMARK_PROTOCOL.md`: working three-track design and resource limits.
  Its referenced `benchmarks/manifests/m6-v1.json` does not yet exist; the protocol is
  not frozen. Planned counts are 216 cells: 108 finite, 72 wallet and 36 inventory,
  including 24 anticipated guarded-model compatibility rejections. These are plans,
  not completed runs. Planned learner seed counts: three for finite, two for typed tracks;
  actual M6 learner seeds executed: zero. Smaller samples limit statistical conclusions.
- `src/blackbox_twin/m6_targets.py`: evaluator-owned finite/wallet/inventory source
  generators, independent wallet/inventory transition specifications and input generation.
  This is unfinished infrastructure, not a verified benchmark implementation.
- `src/blackbox_twin/typed_learning.py`: `initialize` now accepts optional `seed` and
  `equivalence_factory`; defaults preserve its earlier call behavior. This enables the
  planned independent learner/training RNG streams but has not yet been integrated
  into an M6 training runner.

Other staged/unstaged changes belong to the existing project history and were preserved.
No reset, staging, commit, push or Git identity change was performed during recovery.

## Declined operation — affected work remains blocked

Exact proposed path:
`src/blackbox_twin/m6_train.py` inside this project. Read-only inspection confirms the
file does **not** exist. The rejected patch did not leave a partial file. Its proposed
contents were not applied, and no alternate implementation file was created.

The tool's available denial information was: automatic approval review failed because
the usage limit had been reached; the action was not executed because review could not
complete. It explicitly said this was **not a determination that the edit was unsafe**.
There is no evidence of a content-based safety decision or syntax-based rejection.

The proposed file is needed for bounded training adapters, isolated oracle RNG streams,
checkpoint/accounting receipts, explicit inventory compatibility rejection and independent
finite-concrete twins. The pilot and campaign depend on it and have not been launched.
Do not retry via another tool, shell redirection, replacement file, alternate filename
or temporary swap. The normal reviewed file-edit tool remains available; no separate
manual approval override is exposed for this operation. A filesystem permission grant
would not resolve or override the failed usage-based review.

The owner has been asked whether to authorize resubmission through normal review.
Until that direction arrives, only independent inspection, verification and continuation
documentation are permitted. Even authorization to resubmit would not bypass a new
review failure or an active usage limit.

## Verification evidence

Saved prior M6 baseline attempts were inspected, not relabelled successful:

| Check | Actual result |
|---|---|
| Initial full baseline | 129 passed, 1 failed, 149.53 s; persistent-cleanup test's final direct cleanup hit Windows sharing/access errors |
| Existing cleanup recheck | 2 passed, 0 failed, 0.36 s |
| Second full baseline | 129 passed, 1 failed, 215.91 s; failed-refinement test encountered a two-second subprocess termination wait timeout |
| Recovery focused rerun, unchanged tests | 3 passed, 0 failed, 4.75 s: both cleanup tests plus failed-refinement reporting |
| Recovery static development check | Six generated source strings compile: easy, medium, delayed, historical rare, wallet, inventory; public action contracts and input generation succeed |
| Focused lint | FAIL: 14 E501 line-length findings in unfinished `m6_targets.py`; no lint-pass claim |
| Git whitespace | Checks pass; existing LF/CRLF notices are retained separately |

The focused passes do not establish that all Windows timing issues are resolved. No test
or timeout assertion was weakened. No oracle or cleanup source was changed in recovery.
A new full-suite pass is still required before a pilot. The historical 130-pass M5.1
result is historical evidence, not a current full-tree verification claim.

The static check executes no target process and no learner: zero oracle actions/resets.
It is not a pilot. Generated input counts were 40 easy, 40 medium, 50 delayed, 50 rare,
286 wallet and 286 inventory for development-only configurations. These arrays were not
frozen or used as confirmatory evaluations. Inventory's two-counter guarded-inference
gap remains explicit; source compilation does not demonstrate representation support.

Recovery logs are preserved under `evidence/m6-recovery/`; original `work/m6-*` logs and
test directories are retained. No completed expensive benchmark work needs rerunning.

## Next permitted actions

1. Obtain direction on the declined creation, without bypassing normal review.
2. Independently address unfinished target-generator formatting and investigate recurring
   Windows shutdown/teardown behavior as needed; preserve all failure evidence.
3. Only once implementation is legitimately unblocked, complete adapters/runner and tests.
4. Run the small bounded diagnostic pilot, then freeze the actual machine-readable
   protocol and source fingerprints before any confirmatory campaign.
5. Preserve the three tracks, cap-1-through-4 wallet coverage, native StatePrefix default,
   concrete typed baseline, support policy, split accounting and reduced seed design.

No M6 engineering/performance verdict or M7 readiness verdict is issued at this checkpoint.
