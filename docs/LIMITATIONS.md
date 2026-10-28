# Limitations and risk register

| Risk | Current control | Remaining gap / next action |
|---|---|---|
| Finite samples miss behavior | Explicit alphabet, reset probes, separate evaluation | No universal reconstruction/equivalence claim; add adversarial delayed-transition targets |
| Source leakage | Process-only oracle, isolated child imports, import regression test | Same-user filesystem access remains possible; OS-enforced separation is not implemented |
| Untrusted executable | Only owned fixtures, no shell, time/frame/query bounds | No memory/CPU/process-tree sandbox; never use this version on untrusted code |
| False reset acknowledgment | Repeat the alphabet probe after reset; mismatch fails | Finite probes cannot prove reliable reset; broader verification needed for new targets |
| Query accounting bias | Physical counters beneath cache and per-event evidence | Cache hits are aggregated library statistics; per-cache-hit events are not stored |
| Crashes / interruptions | Per-event commits and hypothesis snapshots | No resumable observation table; hard-killed runs may retain `running` status |
| Timing overrun | Check before call and cap response wait | Scheduler, SQLite and process cleanup can exceed soft wall-clock limit; not a hard real-time bound |
| Typed/infinite domains | Action JSON schema; finite declared templates | No amount discovery, monotonicity claims, symbolic references or register inference |
| Easy fixture | Six state-dependent lifecycle modes plus two-state evaluator | Status is highly informative; not evidence of hard hidden-state reconstruction |
| Benchmark leakage | Frozen model, distinct full evaluation words and separate DB | Only one demo seed/family; no statistical superiority claims |
| Export fidelity | Standalone interpreter and real M3 differential/refinement/regression loop | Finite templates only; no general executable synthesis |
| Platform drift | Verified Python 3.12 on Windows; CI configuration supplied | Linux/macOS CI has not executed here |
| Privacy of raw outputs | Synthetic fixture responses only | No general sensitive-output redaction; do not record private targets yet |
| Release/license | Local only, dependency licenses inspected | Owner license decision and full transitive review still required before release |

This project has completed M3 within its declared finite-fixture scope. It has no HTTP adapter, custom planner,
symbolic solver integration, React workbench, full benchmark suite, screenshot/video assets,
or release candidate. No public repository, deployment or release was created.

M3-specific limits: one delayed synthetic target and primary seed demonstrate authentic
refinement, not statistical superiority. Initial equivalence testing is intentionally weak
and explicitly reported. State-cover extensions are bounded tests, not a complete conformance
method. The shrinker establishes deletion-local minimality only when it completes its final
checks; budget-stopped outputs retain a confirmed smaller mismatch without that claim.
Symbolic references fail closed, and arguments are not minimized. A corpus outcome can
remain unresolved after failed relearning. Logical cache hits are library statistics; only
recorded physical calls are charged to oracle budgets. Hard process termination can leave a
run marked `running`; automatic crash reconciliation/resumption remains pending.
