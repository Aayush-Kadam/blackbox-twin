# BlackBox Twin

BlackBox Twin experiments on an unfamiliar stateful program, infers observable behavior,
and generates an independent executable twin. Differential testing finds disagreements;
replay and deletion shrinking produce small counterexamples; active automata learning
refines the model. Typed experiments report uncertainty and unsupported behavior.

It combines **AALpy active automata learning**, JSON-lines subprocess interactions,
SQLite evidence and a local React + FastAPI workbench. No LLM, GPU, paid API or credentials
are needed. Its verified scope is trusted, owned deterministic fixtures. Generated twins
are behavioral hypotheses: neither universal equivalence nor general program reconstruction
is claimed. The project does not introduce a new L* algorithm.

## Quick start

Use Python **3.11 or 3.12**, verified on Windows and Ubuntu. Clone this repository and
run from its root. Production frontend assets are bundled; Node is unnecessary for use.

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-m8-lock.txt
.venv/Scripts/python.exe -m pip install .
.venv/Scripts/python.exe -m blackbox_twin.workbench --project . --runs runs/local-review --port 8765
```

Ubuntu:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-m8-lock.txt
.venv/bin/python -m pip install .
.venv/bin/python -m blackbox_twin.workbench --project . --runs runs/local-review --port 8765
```

Open <http://127.0.0.1:8765/> and choose **Run fresh demonstration** to execute discovery,
shrinking and refinement. Historical replay is separately labelled. Inspect models,
traces, query costs, typed uncertainty and preserved benchmark failures; download an
independent twin. Stop the server with Ctrl+C after work finishes. Three fresh demos
are allowed per output root; the 64 MiB storage admission limit is not an OS quota.

For CLI-only use, `python -m pip install .` installs the core; the web stack is optional.
Use the virtual environment's Python for subsequent commands.

## Executable demonstration

```sh
python scripts/run_m3_demo.py --out runs/m3-demo --evaluation-seed 20261027 --count 100
python -m blackbox_twin.cli --help
```

Use a fresh output directory. Substitute `.venv/Scripts/python.exe` on Windows or
`.venv/bin/python` on Ubuntu for `python`.

The delayed-commit fixture initially produces a one-state hypothesis. Differential
testing discovers a disagreement; replay-validated shrinking reduces ten actions to
`advance, advance, advance, advance, commit`. AALpy learns five states from that
counterexample. Its regenerated twin passes all **35 recorded regression sequences**.
On 100 inputs frozen before learning, complete-trace agreement improves from **73/100
to 100/100**, and output agreement from **1,967/1,996 to 1,996/1,996**.

Learning, discovery, shrinking, refinement and regression replay consume **1,855 physical
oracle actions and 288 resets**; separate paired evaluation consumes **3,992 actions and
200 resets**. Twin costs are recorded separately. This bounded single-target demonstration
is not an overall benchmark or equivalence proof. See the
[phase summary](evidence/m3-demo/loop/summary.json),
[frozen paired evaluation](evidence/m3-demo/evaluation/evaluation.json) and
[counterexample guide](docs/COUNTEREXAMPLES.md).

`bbt learn`, `bbt diff`, `bbt counterexample`, `bbt refine` and `bbt loop` expose
the pipeline; consult each command's `--help` for its contracts and budgets.
Generated `twin.py` files use Python's standard library and the learned table,
without calling the oracle or reading the training database. Keep one JSON-lines
process alive for multi-action sequences; reset uses `{"control":"reset"}`.

## Evidence and limits

The frozen **M6 campaign covered 21 targets, 216 cells and 324 scored points**.
Rare/delayed paths and unseen long typed sequences remain difficult; guarded two-counter
inventory inference is unsupported. Hardened wallet inference made zero measured concrete
errors at reduced coverage and did not beat legacy adaptive fidelity. Abstention is not
successful fidelity. The custom cost-aware ranker underperformed native AALpy baselines;
query-efficiency superiority is unproven.

Typed twins distinguish **observed**, **inferred-supported**, **ambiguous** and
**unsupported** behavior. Unknown transitions invalidate state until reset. This is
bounded inference, not general symbolic execution or a financial integration.

Read [M6 results](docs/M6_RESULTS.md), [failure analysis](docs/M6_FAILURE_ANALYSIS.md),
[typed support policy](docs/M5_SUPPORT_POLICY.md), [prior art](docs/PRIOR_ART.md) and
[trust boundaries](docs/M8_THREAT_MODEL.md). Subprocess bounds and the local server
provide no OS-enforced isolation for hostile code. Concurrent filesystem replacement
during an open remains outside the verified threat model.

This distribution includes a hash-listed curated evidence kit (~5.8 MB), not the full
historical research archive. Historical reports may reference artifacts retained outside
this distribution. Their dated verdicts remain intact; current
[validation results](docs/M82_VALIDATION_RESULTS.md) document later engineering gate closures.

## Verification and development

The planned M0–M8.2 engineering and verification milestones are complete within the
declared limitations. Earlier milestone reports retain their original dated verdicts.

[M8.2 hosted validation](https://github.com/Aayush-Kadam/blackbox-twin/actions/runs/40700717049)
on `a6c8a1053fab3441586795b733b707a616e4f5b5` passed all six jobs:

| Matrix | Executed result |
|---|---|
| Windows / Ubuntu × Python 3.11 / 3.12 | 189 passed per job; zero failures or skips |
| Windows / Ubuntu frontend | 11 tests per job; frozen install, format and production build passed |

All seven physical-link cases passed in every Python job under the strict CI flag.
Each job built and independently installed a wheel into a fresh environment and
reproduced the supported demo, typed labels and unsupported inventory result.
This does not certify every Windows reparse-point type. Existing TestClient and
action-runtime deprecation warnings remain disclosed. Launch-documentation checks are
tracked on the [Actions page](https://github.com/Aayush-Kadam/blackbox-twin/actions).

```sh
python -m pip install -e '.[dev,workbench,workbench-test]'
python -m ruff check src tests fixtures scripts
python -m ruff format --check src tests fixtures scripts
python -m pytest -vv -o faulthandler_timeout=120
```

Frontend development uses Node 22 and pnpm 11.25.0: from `frontend/`, run
`pnpm install --frozen-lockfile --ignore-scripts`, `pnpm test`, `pnpm run build`
and `pnpm run format:check`. No separate semantic JavaScript linter is configured.
See the [developer and independent reproduction guide](docs/DEVELOPER_GUIDE.md),
[architecture](docs/ARCHITECTURE.md) and [current project state](docs/PROJECT_STATE.md).

## License

Original contributions: **Copyright 2026 Aayush Kadam**, licensed under
[Apache License 2.0](LICENSE). Third-party material retains its own terms; preserve
[NOTICE](NOTICE), [third-party attribution](THIRD_PARTY_NOTICES.md) and bundled runtime
license texts. Package-registry publication, public workbench hosting, GitHub Releases
and version tags are outside this source launch.
