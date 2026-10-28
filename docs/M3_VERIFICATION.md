# M3 verification and closure — 2026-10-27

Verdict: **PASS within the declared deterministic, resettable, finite-fixture scope**.
Genuine refinement, held-out evaluation, clean reproduction and evidence audits are verified.
The final post-repair suite passed **62 tests, 0 failed in 77.48 seconds**. No M4 work has
begun; the overall project is not release-ready.

## Objective and implementation

M3 adds real original-versus-executable-twin differential experiments, replay-confirmed
counterexamples, deletion minimization, automatic AALpy relearning, independently generated
replacement twins, regression replay and separate paired evaluation. Models are never
repaired by manually editing transition tables.

New modules are `differential.py`, `experiments.py`, `counterexamples.py`, `refinement.py`,
`m3_evaluation.py` and `m3_cli.py` under `src/blackbox_twin/`. Existing `cli.py` registers
the new commands; `learning.py` supplies recorded samples and confirmed counterexamples
through AALpy's supported interfaces; `oracle.py` preserves process failures during cleanup.
Additional files include the delayed target and its manifest, `test_differential.py`,
`test_refinement.py`, `test_cleanup.py`, `scripts/run_m3_demo.py`,
`scripts/audit_m3_evidence.py`, `benchmarks/manifests/m3-paired.json`, README and documentation.
`test_core.py` retains its behavioral assertions with appropriate non-timeout deadlines.

Existing SQLite schema version 1 and M2 evidence remain intact. M3 versioned JSON records
use the existing artifact table and a portable append-only counterexample corpus. Model
revision manifests preserve parents, counterexample IDs and model/twin hashes. Dynamic
references are rejected rather than incorrectly removed during reduction. Random words,
bounded state-cover extensions, delta debugging and L* are established methods; this is
an engineering integration, not a novelty or query-efficiency superiority claim.

## Baseline and final verification

- Before M3 changes: **24 passed in 48.49 seconds**; M2 evidence audit passed.
- The full suite left running at the usage-limit interruption completed successfully:
  **60 passed, 0 failed in 116.94 seconds** (`evidence/m3-pytest.txt`).
- Continuation inspection confirmed the earlier two failures were actual deadline expiry
  during tests using 150–200 ms for non-timeout expectations. Those cases already use
  the normal **2-second** allowance. Dedicated **150 ms** and **200 ms** timeout cases remain.
  Production defaults were not globally increased and behavioral assertions were retained.
- Repeated targeted verification found an additional real defect: Windows `WinError 32`
  temporary-directory cleanup could mask an already-detected oversized response. The failed
  repeat log remains `evidence/m3-targeted-repeats.txt`.
- Narrow repair: retry only Windows sharing/lock violations (32/33), at most five cleanup
  attempts with a combined 0.75-second backoff. If cleanup still fails, the original
  OracleFailure remains primary and its recorded message includes `cleanup_failure`.
  Ordinary explicit cleanup failures continue to propagate normally.
- Two deterministic regression tests exercise transient directory locks and persistent
  cleanup denial. The corrected fault group ran **three times: 12 passed, 0 failed each**
  (36 executions), including crash, malformed transport, reset failure, oversize and
  dedicated short-timeout cases. Log: `evidence/m3-targeted-corrected-repeats.txt`.
- Latest full suite: **62 passed, 0 failed in 77.48 seconds**, log
  `evidence/m3-closure-pytest.txt`. It includes all prior M0–M2 tests and the real M3 loop.
- Ruff lint: **PASS**. Formatting: **PASS, 26 files already formatted**. No static type checker is configured in
  `pyproject.toml`; no type-check pass is claimed.
- M2 and M3 evidence audits: **PASS**, re-executed during continuation.

Previous failure logs were retained, including `m3-pytest-concurrent-failure.txt`
(57 passed, 2 failed) and the subsequent `m3-pytest-59.txt` successful run. The detailed
Windows scheduling contribution cannot be proved from those logs alone: the evidence shows
expiry before expected output, inappropriate deadlines for non-timeout tests, and successful
repeated checks after the narrow test correction. The separate directory-lock defect was
treated as a real implementation defect and repaired, not dismissed as flakiness.

## Genuine counterexample and model revision

Primary preserved run: `evidence/m3-demo/`.

| Item | Verified evidence |
|---|---|
| Initial revision 000 | **1 state**, ID `693910cfe0460b7f616f094f19af7e0ac2c3cdd86ac1183bb3ddaa81716e0522` |
| Initial search restriction | AALpy random W-method, 1 walk/state, maximum walk length 1; a normally learned incomplete hypothesis |
| Discovered sequence | `idle, commit, advance, advance, advance, idle, advance, commit, commit, advance` |
| First divergence | Action **8** (index 7), JSON pointer `/result`: original `accepted`, old twin `denied` |
| Minimized sequence | `advance, advance, advance, advance, commit` |
| Minimized divergence | Action **5** (index 4), `/result` |
| Minimization work | 32 fresh-reset candidate executions; 168 original actions and 32 resets |
| Revised revision 001 | **5 states**, ID `8b770ad7986ccff34b56738851b6def47cb3d59b59bae0d57476d8227793f03f` |
| Actual refinement | Recorded observations enter AALpy's cache; a confirmed mismatching prefix enters its equivalence-oracle interface; **2 learning rounds** |
| Replayed failures | Both original ten-action and minimized five-action cases agree with the replacement executable twin |
| Regression corpus | **35/35 passed**; all **30** previously passing cases preserved; **0** introduced regressions |

The initial and revised model/twin files remain in `loop/revisions/000/` and `001/`.
Discovery and replay metadata are preserved at
`loop/counterexamples/3c84269c-fd80-43de-99b7-e95b803e9d41/discovery.json`; its numbered
outcome file records resolution. Every reduction is executed against fresh reset original
and twin processes. The result is deletion-local minimality under the implemented procedure,
not a claim of a globally shortest sequence or argument minimum.

AALpy RS counterexample processing requires a differing **final** output. The original
ten-action trace differs earlier but matches at its final action; the adapter correctly
returns the prefix ending at the first divergence. Tests cover that exact integration
trap and a repeated-hypothesis stop guard. No source or private state is supplied to the
learner; a regression test prevents parent-side opening of the hidden fixture source.
The boundary remains architectural rather than an OS confidentiality sandbox.

The full suite includes a real automated end-to-end test. Separate fault-injected twin
and no-progress learner tests validate negative paths and are not counted as authentic
refinement evidence. A second post-refinement search ran 100 seeded words and found no
further mismatch under its bounded policy; this is not an equivalence proof.

## Frozen paired evaluation and reproducibility

The final 100 distinct words, lengths 16–24, use seed **20261027** and were frozen before
initial learning. The loop receives neither that input file nor its reference outputs.
The evaluator uses the same words for both executable versions and checks that original
reference traces agree across passes. The audit confirms zero full-word training overlap.
Shared prefixes and transitions are allowed and are not described as statistical independence.

| Metric | Before refinement | After refinement |
|---|---:|---:|
| Exact complete traces | **73/100** | **100/100** |
| Exact output steps | **1,967/1,996** | **1,996/1,996** |
| Per-step agreement | **98.5471%** | **100%** |
| Unsupported traces in the finite alphabet | 0 | 0 |

This is one functional synthetic-target/seed comparison, not a multi-seed superiority
benchmark or proof of unrestricted behavior. Its `denied` replies are result values,
not `error` payloads, so this set does not establish error-code fidelity by itself.

`evidence/m3-clean-reproduction/` preserves an independently installed non-editable run.
Continuation inspection confirmed imports from `work/clean-venv/Lib/site-packages`,
`direct_url.json` with an empty `dir_info` (no editable flag), and working CLI help.
The audit verifies equal behavioral tables excluding provenance, equal physical query
counts, and the same paired scores. This adequate reproduction was preserved rather than
rerunning the expensive experiment. The final cleanup-only repair is checked by the new
fault regressions and fresh end-to-end tests; it does not change inference or comparison.

## Physical query accounting

| Original-oracle phase | Actions | Resets |
|---|---:|---:|
| Initial learning including reset probes | 26 | 12 |
| Initial differential discovery | 34 | 7 |
| Counterexample minimization | 168 | 32 |
| Refinement learning/search | 786 | 102 |
| Regression replay | 163 | 35 |
| Subsequent differential search | 678 | 100 |
| **Loop subtotal** | **1,855** | **288** |
| Separate paired held-out evaluation | **3,992** | **200** |
| **Primary demonstration total including evaluation** | **5,847** | **488** |

Twin executions are separate: **5,035 actions / 374 resets**, including paired evaluation.
Initial/refinement library cache statistics are **3 / 59 logical saved queries**; they are
not physical action savings. Every physical event is assigned an original or `twin:` phase.
Per-iteration and cumulative accounting are in `loop/summary.json`; SQL counts are audited.

Recorded primary wall time: **18.640 s** loop + **37.625 s** evaluation = **56.265 s**,
excluding installation and tests. Non-editable reproduction recorded **29.031 + 59.328 =
88.359 s** with identical query counts. These local timings include recording/inference
overhead and concurrent machine activity; they are not controlled performance benchmarks.
Additional CLI validations are separately recorded: guided discovery **436/122**,
standalone shrinking **60/16**, and imported-model refinement **1,200/233** original
actions/resets. The latter preserved **122/122** observed traces, including 121 previously
passing cases. Their artifacts are `evidence/m3-cli-guided`, `m3-cli-minimized` and
`m3-cli-refined`. Test/development queries are not included in the primary demo total.

## Reproducible commands

From the enclosing workspace, with the existing development environment:

```powershell
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m3-closure-tests
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_evidence.py
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m3_evidence.py
```

The repeated fault group used `test_core.py`, `test_differential.py`, `test_cleanup.py`
with `-k 'transport_failures or real_process_failure_classification or cleanup_failure_cannot_mask or directory_lock_retries'`
three sequential times, with distinct workspace-owned temporary directories.

The already-executed main demo command was:

```powershell
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/run_m3_demo.py --out outputs/blackbox-twin/evidence/m3-demo --evaluation-seed 20261027 --count 100
```

For a reproduction, choose a new output directory; never overwrite the preserved evidence.
Project-relative installation and individual CLI examples are in README and
`COUNTEREXAMPLES.md`. No static type-check command is configured. No public CI run,
publication, push or release was performed.

## Remaining limits and next step

Finite declared templates and deterministic resettable owned fixtures only. Dynamic
references and argument minimization are unsupported. Local deletion minimality is not
global minimality. Process time/frame/query bounds do not constitute OS memory/CPU or
filesystem isolation. Cross-platform CI, broader benchmarks, resumable learning and
hard-kill reconciliation remain future work. Persistent cleanup denial remains a visible
failure; transient retries do not guarantee that external directory locks will clear.
Git author identity is unset; the existing staged tree is preserved and no identity invented.

M3 is closed as PASS within this scope. The staged tree remains
`9d804578899a21849533231252b1a2fbb7e23059`, unchanged during the continuation; this is a tree
ID, not a commit. M4 may begin only after the owner's next authorization. No M4
implementation belongs to this continuation.
