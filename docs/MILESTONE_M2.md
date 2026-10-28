# M2 — First behavioral reconstruction

**Gate: PASS WITH LIMITATIONS.** Genuine baseline learning and finite-sample prediction
are verified. No original-algorithm, query-efficiency or equivalence claim is supported.

Objective: infer a Mealy hypothesis from process observations, cache logical queries,
serialize it and compare new sequences with the target. Implemented: RecordedSUL,
AALpy L*, standard RandomWMethodEqOracle, physical-budget enforcement beneath caching,
hypothesis checkpoints, strict total-machine JSON, separate held-out CLI evaluation,
tiny known-machine recovery, and standalone Python export as an M3 prerequisite.
Changed files: `src/blackbox_twin/learning.py`, `contracts.py`, `evaluation.py`,
`synthesis.py`, `cli.py`, `fixtures/targets/toggle_process.py`, `tests/test_core.py`,
`tests/test_adversarial.py`, `scripts/audit_evidence.py`, `evidence/` artifacts.

Decisions: preserve established library behavior and clearly label randomized equivalence
approximation; freeze the model before a separate evaluation run; exclude full training
words while allowing prefix reuse; use neutral state IDs and unsupported-model outputs.

Executed result: seed 7 learned **6 states** in **1 L* round**, using **2,004 physical actions**
and **368 resets**, including reset probes. AALpy reported 216 membership queries, 864
membership steps, 150 search queries, 1,128 search steps and 6 logical cache hits. Recorded
library time: 8.5 seconds learning + 9.11 seconds search = 17.61 seconds; this includes
recording overhead and is not a laptop performance guarantee. Oracle interaction time
was approximately 0.871 seconds. Separate seed-2027 evaluation: **100/100 traces**, length
9–20; **1,492/1,492 outputs**; **1,036/1,036 target-error outputs**. Counts and zero
full-sequence overlap were independently checked from SQL.

Tests: tiny two-state fixture agrees with evaluator-only truth on all **62 nonempty words
through length 5**. Order tests cover 81 four-action words in a three-symbol subalphabet
and 25 additional longer samples. Standalone twin executes in an empty working directory
without target/DB imports. Final suite: **24 passed**, lint/format passed. Exact commands
and all evidence paths are in `VERIFICATION.md`.

Limits/risks: one simple demo family/seed; no fairness comparison or uncertainty study;
source boundary is architectural rather than an ACL sandbox; no typed amounts/references;
the single-round order run does not demonstrate refinement. Cached hits are aggregate
statistics. A complete model may not exist when a small budget expires. A full M3 gate
requires real disagreement, replayed shrinking and automatic refinement, all still pending.
Next milestone: M3, starting with a delayed-distinguishing target and durable regression cases.
