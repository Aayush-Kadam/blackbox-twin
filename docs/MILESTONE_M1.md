# M1 — Real black-box interaction

**Gate: PASS WITH LIMITATIONS** for trusted owned local fixtures. Process isolation does
not provide a secure environment for unknown or hostile binaries.

Objective: execute real stateful requests through a generic interface and retain auditable
costs and replayable outcomes. Implemented: JSON-lines adapter, acknowledged resets,
repeated reset probes, bounded frames/queues/time/query counts, transport error categories,
exact target outputs, physical counters, SQLite events and JSONL export, CLI replay.
Changed files: `src/blackbox_twin/oracle.py`, `storage.py`, `cli.py`, `contracts.py`,
`fixtures/targets/order_process.py`, `examples/order_processing/target.json`,
`tests/conftest.py`, `tests/test_core.py`, `tests/test_adversarial.py`.

Decisions: keep a persistent subprocess with explicit reset; no shell; isolated Python
imports; writable workspace temporary directories; count attempted calls before transport;
commit each event. Target errors remain learner-visible responses. Startup and cleanup
failures retain failure status; hard-kill reconciliation is not implemented.

Commands/results: CLI replay produced a rejected unauthorized capture, then successful
authorization/capture and status. Query/reset/sequence limits, replay equality, invalid
reset acknowledgment, false acknowledgment, EOF, malformed/oversized output and timeout
cases passed in the **24-test** final suite. Export succeeded and the SQL/event count audit
passed. Exact commands: `VERIFICATION.md`. Evidence: `evidence/demo-replay.sqlite`,
`evidence/clean-install-replay.sqlite`, `evidence/demo-training-v2/events.jsonl`,
`evidence/pytest.txt`, `evidence/audit.json`. No M1 comparative benchmark.

Limits/risks: no OS memory/CPU/process-tree limits; no arbitrary remote/HTTP/binary support;
raw records are appropriate only for these synthetic non-sensitive fixtures; finite reset
probes are not a proof. The failed system-temp run is retained with an explanation.
Next milestone: M2 (implemented and verified; see its report).
