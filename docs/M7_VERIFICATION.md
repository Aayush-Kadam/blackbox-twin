# M7 verification — 2026-10-27

**M7 PASS WITH LIMITATIONS. M8 READY WITH LIMITATIONS.** Implementation, successful
tests and controlled demonstration results are distinct from the preserved M6 scientific
verdict. No new confirmatory campaign was run, and no M8 work or publication started.

## Implemented and exercised

React frontend / FastAPI backend, an allowlisted experiment registry, actual learned-state
graphs and transition inspection, original/twin comparisons with first-divergence highlighting,
original/minimized counterexamples, before/after model inspection, separate original/twin
and training/evaluation costs, paginated physical event inspection, validated model/twin
downloads, fixed bounded live demonstration and typed-support preview with provenance.
The benchmark explorer exposes all 324 M6 points, including unsupported and non-qualifying
ones, without turning empty accuracy denominators into perfect scores.

The original M7 specification was recovered from the roadmap and master build prompt:
an interactive scientific workbench using FastAPI and React. The implementation follows
that scope and reuses the existing M3/M5.1 components. No existing learning module changed.

## Fresh demonstrations and costs

Three new complete demonstrations were executed sequentially, outside the test-suite traffic:

| Run | Meaning | Wall time |
|---|---|---:|
| `runs/m7-primary` | First fresh CLI development execution | 48.306 s |
| `runs/m7-live/live-bb4f6a1d66fb440da8b54a00ceb82de0` | Actual browser-triggered live execution | 50.338 s |
| `runs/m7-clean-reproduction` | New non-editable installation | 56.623 s |

Every run recorded identical costs and behavior:

| Side / phase | Actions | Resets |
|---|---:|---:|
| Original learning/search/shrink/refinement/regression | 1,855 | 288 |
| Separate original paired evaluation | 3,992 | 200 |
| Twin during search/shrink/regression | 1,043 | 174 |
| Twin during paired evaluation | 3,992 | 200 |
| Additional isolated final-twin replay | 5 | 1 |

All three together used **5,565 original training actions / 864 resets**, plus **11,976
separate original evaluation actions / 600 resets**. Total original demonstration cost:
17,541 actions / 1,464 resets. Summed demonstration wall time: 155.267 seconds. Test-suite
fixture queries are additional verification traffic, not included in these demonstration
totals; their aggregate query cost was not collected. Policy previews make zero original
queries. No peak-memory measurement or memory-efficiency claim is made.

The weak initial learner produced one state. Real differential search discovered a
10-action disagreement with first divergence at zero-based index 7. Replayed deletion
minimization produced `advance, advance, advance, advance, commit`, first divergence at
zero-based index 4 (displayed as step 5). Automatic refinement produced five learned states.
35/35 regression cases passed; 30/30 previously passing cases were preserved, with zero
new regressions. On 100 distinct frozen sequences, initial exact traces were 73/100 and
outputs 1,967/1,996; refined traces 100/100 and outputs 1,996/1,996. Full-word training
overlap was zero. This reproduces a supported M3 demonstration, not a new performance
benchmark, a novel algorithm or an equivalence proof.

`live-audit.json` and `clean-audit.json` independently reconcile physical action/reset
and phase counts, score numerators/denominators, model/twin hashes, counterexample traces,
regressions, frozen-input creation before training and absence of evaluation-word overlap.
Both final runs recorded source/fixture/input hashes before learning. The first CLI run
predates that wrapper metadata addition and is retained as development evidence.

## Python and frontend tests

- Complete Python suite: **154 passed, 1 warning in 245.26 seconds**. The unchanged
  M0–M6 tests are included; no subprocess timeout, cleanup protection or assertion was
  weakened. Thirteen new M7 tests cover serialization, export integrity, trace comparison,
  divergence and counterexample presentation, all support categories, abstention/state
  invalidation/reset, independent twin execution, physical cost reconciliation, read-only
  pagination, preserved benchmark failures, bounded requests, Host/origin/path restrictions,
  explicit job failure and single-worker lifecycle cleanup.
- After the final M7 metadata/provenance/request-limit edits, the affected M7 suite passed
  again: **13 passed, 1 warning in 2.07 seconds**. Preexisting engine sources were unchanged.
- The warning is Starlette TestClient's deprecated `anyio.abc.BlockingPortal` alias. It
  was retained in the logs, not suppressed or represented as a failure.
- Frontend: **11 tests passed, zero failures**, including actual React server rendering
  of persisted original/minimized counterexamples and learned-state models, four visible
  support labels, null-denominator formatting, refusal reporting and inventory failure rows.
- Production React build passed. Prettier check passed. Python Ruff lint passed and
  **70 files** passed its formatting check. No type checker or frontend ESLint configuration
  is present; no pass is claimed for either.

One initial new test incorrectly expected `status:accepted`; the real fixture returns
`result:accepted`. That test failed (12 passed / 1 failed), was corrected to the actual
contract, and passed subsequently. The first UI reader also incorrectly combined original
and twin physical events in M3's shared database. It failed closed with an accounting
error; the reader now partitions by recorded `twin:` phases, with an explicit regression
test. Neither issue was hidden by changing historical evidence.

## Actual browser checks

The locally served production build was exercised through a real browser, including:

- Historical replay and revision switching, with real one-/five-state graphs.
- Fresh demo launch, running/disabled control, completion, new experiment selection and
  the persisted before/after scores and costs.
- Inferred-supported prediction, ambiguous refusal, subsequent unsupported action and
  trusted reset restoring an observed prediction.
- Invalid JSON showing an explicit error and clearing stale preview results.
- Inventory filtering with zero coverage, undefined accuracy, unsupported status and
  non-qualifying results retained. No application console errors were captured.

Screenshots and accessibility transcripts are in `evidence/m7-verification/browser/`.
The browser download prompt was not exercised; the actual export HTTP bytes/headers
were verified in backend tests. Mobile behavior and cross-browser/platform coverage were
not verified. An external unfamiliar-developer usability study was not performed.

![Fresh browser-triggered demonstration](../evidence/m7-verification/browser/fresh-demo.png)

## Fresh non-editable installation

A new `work/m7-clean-venv` was created with Python 3.12.10. An offline wheel build/install
of `blackbox-twin[workbench,workbench-test]` succeeded. Installation metadata has no editable
flag, and the imported module is under that environment's site-packages. The installed
package independently retrained and refined the supported demonstration; both model
transition tables (excluding run-specific provenance), physical counts and frozen scores
matched the browser run. Its final twin ran with `python -I -S` in a directory containing
only `twin.py`, with no original process or BBT import. This demonstrates executable
independence, not OS-enforced source inaccessibility.

Installed HTML, JS, CSS and bundled license notices matched source build hashes, and the
installed FastAPI app served them successfully. Its API loaded historical data, all four
typed statuses and all 324 M6 points. See `runs/m7-clean-reproduction/reproduction.json`.

Exact executed installation/reproduction commands, from the workspace root:

```powershell
$env:UV_CACHE_DIR="$PWD/work/uv-cache"
$env:TEMP="$PWD/work"
$env:TMP="$PWD/work"
uv venv --python work/.venv/Scripts/python.exe work/m7-clean-venv
uv pip install --offline --python work/m7-clean-venv/Scripts/python.exe 'outputs/blackbox-twin[workbench,workbench-test]'
work/m7-clean-venv/Scripts/python.exe -I outputs/blackbox-twin/scripts/reproduce_m7.py --project outputs/blackbox-twin --compare outputs/blackbox-twin/runs/m7-live/live-bb4f6a1d66fb440da8b54a00ceb82de0 --out outputs/blackbox-twin/runs/m7-clean-reproduction
```

Those output/environment paths now exist. Use fresh names for any further reproduction;
completed evidence is not overwritten. API/CLI usage and frontend rebuild commands are
in `M7_WORKBENCH.md`. Verification commands:

```powershell
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m7.py --project outputs/blackbox-twin --run outputs/blackbox-twin/runs/m7-live/live-bb4f6a1d66fb440da8b54a00ceb82de0
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m7.py --project outputs/blackbox-twin --m6-only
```

## Preserved science and remaining gates

All preexisting M6 engine-source hashes match the frozen protocol. M6 artifact integrity
and cell/result reconciliation are separately recorded in `m6-preservation.json`; this
read-only check makes no new oracle calls. M6's 21 targets / 216 cells / 324 checkpoints,
214,815 training actions / 51,022 resets and 138 unreached cells remain intact. Adaptive
wallet's 97.38% aggregate median trace fidelity, hardened conditional accuracy/abstention,
rare/delayed failures, unsupported inventory and lack of query-efficiency superiority
remain the established findings. No isolated inventory replay is relabelled as success.

M7 is ready to enter M8 **with limitations**: Windows desktop is the only verified platform;
broader security/dependency/license review, profiling and CI workbench/frontend wiring
remain pending. No hostile-code execution, OS containment, peak-memory bound, universal
equivalence, external usability certification or general-purpose software cloning is
claimed. The local server was stopped after completed verification. `cleanup.json` records
zero Python processes in the native process list and a refused connection to local port
8765. An initial CIM enumeration was unavailable and was not used to infer absence; the
final check used the native process list and a direct socket connection. The test covers
normal lifecycle cleanup; forced shutdown during active work is not asserted as an
OS-enforced guarantee. The frozen-lockfile frontend install also completed successfully
with scripts disabled, and all 19 Python workbench lock versions matched the clean environment.

The existing Git index SHA256 remained
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
No staging, commit, push, publication, visibility change or remote resource occurred.
Installation attempts initially encountered a cache write failure, a registry connectivity
failure, Windows pnpm global-store symlink failures and an ignored install-script notice;
the workspace cache, granted network access and contained store resolved installation.
esbuild built without enabling its install script. No file-edit review was denied or bypassed.

Technical references used while implementing the local transport/rendering:
[FastAPI file responses](https://fastapi.tiangolo.com/advanced/custom-response/) and
[React createRoot](https://react.dev/reference/react-dom/client/createRoot). These describe
APIs, not the project's experimental findings.
