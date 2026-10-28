# BlackBox Twin

M8 hardens the local **React + FastAPI scientific workbench** driven by real persisted evidence.
Run a fresh bounded M3 discovery/shrink/refinement flow, inspect learned models and traces,
download independent twins, explore typed uncertainty, and examine the preserved M6 failures.
**M8.2: PRIVATE RELEASE-VALIDATION CANDIDATE.** Original contributions are licensed
under Apache-2.0, Copyright 2026 Aayush Kadam. Third-party notices remain separate.
Public release, public hosting and visibility changes are not authorized.

Historical M8.1 result: **NOT READY for public release.** The fresh frontend-install gate is closed;
runtime notices and a reviewed distribution inventory are prepared. Project licensing,
physical link/junction verification and actual hosted CI/Linux execution remain gates.
See [M8.1 release readiness](docs/M8_1_RELEASE_READINESS.md) and the preserved
[M8 verification](docs/M8_VERIFICATION.md).
The license decision was subsequently approved in M8.2; historical reports retain their
dated pre-approval status. See LICENSE, NOTICE and the current licensing record.

From an installed environment at the repository root, open http://127.0.0.1:8765/:

```powershell
python -m blackbox_twin.workbench --project . --runs runs/local-review --port 8765
```

Choose **Run fresh demonstration** for actual execution, or inspect the labelled historical
replay. See the current [installation and reproduction guide](docs/DEVELOPER_GUIDE.md),
[trust boundaries](docs/M8_THREAT_MODEL.md) and [dependency review](docs/M8_DEPENDENCIES.md).
Historical [M7 verification and costs](docs/M7_VERIFICATION.md) remain intact. The server is local
only; stop it after active work completes. Core CLI use does not require the optional web stack.

M6 completed a frozen 21-target campaign: 216 cells / 324 scored points, with physical
accounting and independent executable audits. **Engineering PASS WITH LIMITATIONS;
M7 READY WITH LIMITATIONS.** Finite rare/delayed paths and unseen long typed sequences
remain difficult; two-counter guarded inventory inference is unsupported. Hardened
wallet inference made zero measured concrete errors but lost coverage and did not beat
legacy adaptive fidelity. See [M6 results](docs/M6_RESULTS.md),
[failure analysis](docs/M6_FAILURE_ANALYSIS.md) and [verification](docs/M6_VERIFICATION.md).
That was the M6 closure verdict; the later M7 implementation is described above.

M5.1 adds evidence-aware typed twins: observed, inferred-supported, ambiguous and unsupported
behaviors are distinct. Unknown transitions invalidate state until reset. Use
`bbt typed-harden --protocol <frozen-protocol> --out <fresh-folder>` for the version-3
wallet flow; `bbt typed` retains the historical M5 comparison. See the
[support policy](docs/M5_SUPPORT_POLICY.md), [diagnosis](docs/M5_1_DIAGNOSIS.md) and
[M5.1 verification](docs/M5_1_VERIFICATION.md). Engineering PASS in its bounded class;
The historical M5.1 gate was M6 READY WITH LIMITATIONS. Abstention is not successful fidelity.

M5 implements a bounded local typed-wallet reconstruction pipeline: typed values,
experimental guard/update fitting, standalone twins and replay-validated refinement.
**PASS WITH LIMITATIONS:** one evaluation configuration generalizes correctly; another
exposes unresolved boundary ambiguity and worse unseen-sequence fidelity than the fixed
grid. See [M5 verification](docs/M5_VERIFICATION.md), [results](docs/M5_EXPERIMENTS.md),
[model specification](docs/M5_MODEL_SPEC.md) and [frozen contract](docs/M5_WALLET_CONTRACT.md).
Run `bbt typed --out <fresh-folder>` from the project setup; this is a synthetic local
experiment, not a financial integration or general symbolic learner.

M4.1: native AALpy StatePrefix is the recommended `bbt learn` default; all other methods
remain available through `--strategy`. The custom cost-aware ranker is experimental and
currently underperforming. See [diagnosis](docs/M4_1_DIAGNOSIS.md) and
[M5 readiness](docs/M5_READINESS.md). M4's negative performance verdict is unchanged;
the later M5/M6 milestones are documented above.

Learn a finite-state behavioral hypothesis from recorded interactions with an owned local
program, then test its predictions against fresh experiments.

This early CLI implementation uses **AALpy L*** and its randomized W-method testing oracle.
It does not claim a new learning algorithm, arbitrary program reconstruction, or proven
equivalence. See [prior art](docs/PRIOR_ART.md) and [limitations](docs/LIMITATIONS.md).

## M2 foundation demonstration

The order fixture accepts create, authorize, capture, refund, cancel and status. The learner
invokes it through a persistent JSON-lines subprocess; it does not import its implementation.
For example, `create, capture` observes a rejection, while `create, authorize, capture`
observes a successful capture. AALpy learns composable state transitions from these outputs.

Verified run: six learned states, 2,004 physical oracle actions and 368 resets. A separate
evaluation matched 100/100 distinct unseen full sequences (1,492/1,492 outputs). This is
a single finite-alphabet smoke run, not a comparative benchmark or an equivalence proof.
Evidence: [training summary](evidence/demo-training-v2/summary.json),
[learned model](evidence/demo-training-v2/model.json),
[held-out result](evidence/demo-heldout/evaluation.json).

## M3: discover, shrink and refine

M3 gate: **PASS** within the declared finite-fixture scope. Final closure checks:
**62 tests passed, 0 failed**; lint, formatting and both evidence audits passed.

The delayed-commit fixture hides a longer distinguishing history. With a deliberately
small initial equivalence search, AALpy learns a one-state hypothesis. Seeded differential
testing executes its generated twin independently and finds a real disagreement. Replayed
deletion minimization reduces ten actions to `advance, advance, advance, advance, commit`.
AALpy then incorporates the observed counterexample and learns five states; no transition
is patched by hand. The regenerated twin passes all 35 recorded regression sequences.

On the same 100 inputs frozen **before learning**, complete-trace agreement improves from
73/100 to 100/100, and output agreement from 1,967/1,996 to 1,996/1,996. This is a functional
single-target demonstration, not an M6 benchmark or a proof of equivalence. Initial learning,
search, shrinking, relearning and regression replay use 1,855 original-oracle actions;
separate paired evaluation uses 3,992 more. Twin execution costs are reported separately.

```powershell
.venv/Scripts/python.exe scripts/run_m3_demo.py --out runs/m3-demo --evaluation-seed 20261027 --count 100
```

Read the [M3 verification report](docs/M3_VERIFICATION.md) and
[counterexample/refinement guide](docs/COUNTEREXAMPLES.md). Preserved evidence includes
[both model versions and phase costs](evidence/m3-demo/loop/summary.json),
[paired evaluation](evidence/m3-demo/evaluation/evaluation.json) and
[independent evidence audit](evidence/m3-audit.json).

## M4: measured experiment selection

**Engineering: PASS WITH LIMITATIONS. Performance hypothesis: NOT SUPPORTED.**
Four baselines, a cost-aware planner and three ablations were compared on three families
and five paired seeds: 120 confirmatory runs, four checkpoints per run, and the same 80
frozen evaluation words within each pair. The proposal had zero paired AULC wins against
either native AALpy baseline, reached 95% fidelity in 13/15 cases versus their 15/15, and
incurred more training wall time. No query-efficiency benefit is advertised.

```powershell
.venv/Scripts/bbt.exe benchmark run --manifest benchmarks/manifests/m4-confirmatory.json --out runs/m4
.venv/Scripts/bbt.exe benchmark audit --out runs/m4
```

Read [protocol and method comparison](docs/M4_EXPERIMENT_PROTOCOL.md),
[measured results](docs/M4_RESULTS.md) and [verification](docs/M4_VERIFICATION.md).
Inspectable artifacts: [summary](evidence/m4-confirmatory/summary.json),
[checkpoint CSV](evidence/m4-confirmatory/results.csv),
[SQL/hash/score audit](evidence/m4-confirmatory-audit.json),
[six-cell installed reproduction](evidence/m4-reproduction/summary.json).
An earlier complete negative pilot is preserved separately, with its seed-separation
amendment disclosed. Process, cache and training records are isolated per run;
paired evaluation references are shared intentionally.

## Install and run

Python 3.11+ is required; Python 3.12.10 on Windows was verified. From this repository:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e '.[dev]'
.venv/Scripts/bbt.exe inspect examples/order_processing/target.json
.venv/Scripts/bbt.exe learn --target examples/order_processing/target.json --budget 10000 --out runs/train
.venv/Scripts/bbt.exe evaluate --target examples/order_processing/target.json --model runs/train/model.json --training-db runs/train/observations.sqlite --out runs/eval --count 100 --seed 2027
.venv/Scripts/bbt.exe replay --target examples/order_processing/target.json --out runs/replay.sqlite create capture authorize capture status
.venv/Scripts/bbt.exe export runs/train/observations.sqlite runs/train/events.jsonl
```

On POSIX, replace `.venv/Scripts/bbt.exe` with `.venv/bin/bbt` and the Python path similarly.
Those platforms have not been executed in this session. Ordinary `python -m venv .venv`
and `python -m pip install -e '.[dev]'` also work where pip/ensurepip are available; this
environment used uv because ensurepip failed. If Windows cache/temp locations are denied,
set `UV_CACHE_DIR`, `TEMP` and `TMP` to a writable workspace directory before installation.
Every learning/evaluation output directory must be new or empty.

Learning automatically writes `model.json`, `twin.py`, `summary.json`, `config.json` and
`observations.sqlite`. Budget exhaustion exits 2, records the stop and preserves any complete
hypothesis; it may occur before a first model exists. An evaluation disagreement exits 3.

## Standalone twin

[The generated demo twin](evidence/demo-training-v2/twin.py) runs with Python's standard
library alone. Copy it to an empty directory and send JSON requests on stdin:

```powershell
'{"operation":"create","arguments":{}}' | python -I runs/train/twin.py
```

Use one persistent process for multi-action sequences. Reset uses
`{"control":"reset"}`. Unsupported concrete inputs return a distinct `bbt_unsupported`
result. The twin executes the learned transition table; it never calls the oracle or reads
the training DB. Automatic differential discovery, shrinking, regression replay and
AALpy-based refinement are now available through `bbt diff`, `bbt counterexample`,
`bbt refine` and `bbt loop`. Use `--help` for actual arguments.

## Tests and architecture

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests fixtures
.venv/Scripts/python.exe -m ruff format --check src tests fixtures
```

Core modules separate strict contracts, bounded process transport, SQLite events, learning,
frozen-model evaluation, standalone generation and CLI. No GPU, paid API, web server or LLM
is required. Only trusted, owned deterministic fixtures are supported; this is not a sandbox.

Read [model semantics](docs/MODEL_SPEC.md), [architecture](docs/ARCHITECTURE.md),
[evaluation protocol](docs/BENCHMARK_PROTOCOL.md), [roadmap](docs/ROADMAP.md),
[verification](docs/VERIFICATION.md), and [continuation state](docs/PROJECT_STATE.md).

## License and publication

No project license has been assigned pending the owner's choice. Installed AALpy and Pydantic
report MIT licensing; that does not replace a complete release dependency review. The
repository is local and unpublished. M3 is verified within its finite-fixture scope;
M4's bounded engineering pilot is verified with limitations and a negative performance
result. M5–M8 are not complete.
