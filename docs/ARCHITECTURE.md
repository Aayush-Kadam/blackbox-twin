# Architecture and trust boundary

`CLI -> Session -> ProcessOracle -> owned JSON-lines executable`

`Session -> Recorder (SQLite)`

`AALpy L* -> RecordedSUL -> Session`

`Hypothesis -> validated BehavioralModel JSON -> standalone twin`

`Separate evaluate invocation -> frozen model + fresh target process -> evaluation DB`

The learning module imports no target implementation and receives no ground-truth model.
The launcher resolves a declared executable and fingerprints it for provenance; its bytes
are not passed to the learning algorithm. Child processes use Python isolated mode, an
empty temporary working directory, argument arrays and no shell. Fixture source remains
in the repository for independent reproduction. This separation prevents accidental
imports in this implementation; it is **not an OS-enforced source confidentiality boundary**.
A malicious learner running as the same Windows user could read repository files.
Do not claim source inaccessibility against an adversarial process.

Protocol/resource controls: one child per session; 1,024-byte requests; 65,536-byte
response frames; a two-item reader queue; per-call timeout; physical action/reset budgets;
sequence length and total run timeout; child termination and cleanup. No inherited Python
search path is used in the target. stderr is discarded and no credentials are required.
The child still has same-user file/network rights and no Windows Job Object memory/CPU or
process-tree enforcement. Only trusted owned fixtures are supported. HTTP and arbitrary
binaries are deferred. A manifest authorization string is an attestation, not a security
permission checker.

Session counts attempted physical actions/resets before execution, including failed calls.
Counts below AALpy caching are authoritative. SQLite records each action/reset immediately,
with request, response, elapsed time, experiment ID and outcome. Experiment/run statuses
record failures and budget stops. No mid-table AALpy resume is offered. Hypotheses are
checkpointed before equivalence search; a budget stop before the first complete hypothesis
legitimately has no model. A checkpoint is not necessarily a successful learning run.

The core imports neither FastAPI nor React. Transport, recording, contracts, learning,
evaluation, generation and CLI occupy separate modules. SQLite schema `user_version=1`
is initialized for new databases; unknown versions fail closed. Future migrations must
be explicit; no historical schema upgrades are currently needed or implemented.

## M7 local workbench

`Bundled React -> loopback FastAPI -> allowlisted read-only Evidence projections`

`Explicit fresh-demo request -> one bounded worker -> unchanged M3 run_loop + evaluate_pair`

`Typed JSON preview -> saved version-3 supported_step -> support/provenance; no oracle`

`Validated revision export -> standalone twin/model attachment`

The optional `workbench.py` transport does not enter core CLI imports. React assets are
compiled locally and included as package data, with no runtime CDN or separate Node server.
Evidence paths resolve within configured roots; original M3/twin events are partitioned
by recorded phases for physical accounting. Model/twin exports verify persisted hashes.
Original M6 source modules and evidence remain unchanged; the explorer reports original
metrics, null denominators, compatibility rejection and criterion failure explicitly.

Only the fixed owned delayed fixture can be launched; clients cannot submit executable
paths, targets, seeds or budgets. Fresh UUID run folders preserve prior work. The worker
admits one job; normal application shutdown waits for bounded session cleanup. Requests
validate Host, same-origin mutation, a local header, content length and a 32-KiB body cap.
Typed sequences have at most 30 requests and start from reset. Unknown-effect actions
invalidate state until trusted reset. Preview metadata caps displayed physical evidence
rows and explicitly marks truncation.

These controls do not establish OS-enforced isolation or a public-service security model.
No arbitrary program upload, remote execution, cross-user authentication, Job Object
containment, verified peak-memory bound or forced active-worker termination guarantee
is implemented. Fresh runs have their own query budgets and preserve failure evidence.
The M7 interfaces do not claim to solve two-counter inventory or prove equivalence.

## M3 extensions

`DifferentialRunner` resets and executes an original Session and a separately generated
twin Session. Versioned comparisons retain parsed raw JSON and identity-normalized payloads,
first divergence, JSON pointers and failure side/stage. Transport failures and unsupported
twin results never qualify as behavioral counterexamples. Physical twin calls have `twin:`
phase names and a separate cumulative counter, shared across twin-process replacements.

Two planners provide seeded random words and state-cover access sequences with bounded
alphabet extensions. These are established testing policies, not a new planning algorithm
or a complete W-method conformance guarantee. Delta debugging and a single-deletion fixed
point replay every candidate after reset. Dynamic-reference contracts are rejected before
shrinking; argument/binding minimization remains outside the supported abstraction.

`run_loop` freezes each model in its own revision folder, generates a standalone interpreter,
persists a confirmed corpus case and relearns with AALpy's supported observation cache and
equivalence-oracle interface. A complete trace is truncated at its first mismatch when
returned as a Mealy counterexample: AALpy's RS processor requires a differing final output.
Every previous physical observation in the run is checked again against the new executable
twin. Imported models require an explicit prior-observation corpus; imported held-out
databases are rejected. Imported observations are copied as provenance, not counted as new
physical calls. A repeated hypothesis/counterexample pair or 100-hypothesis cap stops learning.

Corpus discovery records are immutable JSON; numbered outcome files append resolution,
failure or budget-stop status. SQLite schema remains version 1: existing generic artifacts
store versioned comparison, minimization, model and summary records. M2 databases remain
readable and their existing evidence files are unchanged.

Paired evaluation is a separate call. A fixed input set is generated before learning;
neither its inputs nor outputs enter `run_loop`. Evaluation rejects full-word overlap with
the supplied training DB, runs the original and both executable twins, and checks that
reference outputs stayed the same between the two passes. Model/twin hashes and parent IDs
link revision artifacts. Run IDs, timestamps and resulting model content IDs legitimately
differ on reproduction; behavior and query counts can still reproduce.
