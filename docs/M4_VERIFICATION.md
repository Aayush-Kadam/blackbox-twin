# M4 verification — 2026-10-27

**Engineering: PASS WITH LIMITATIONS. Performance hypothesis: NOT SUPPORTED.**

The engineering pilot and M3 integration work; the measured planner does not reliably
outperform credible native policies. The limited verdict reflects fixed-manifest pilot
scope, top-budget ceiling rather than universally exact spending, and suite-cell rather
than live learner/evaluator interruption recovery. It is not a euphemism for a positive
performance result. M5 is not started.

## Baseline, files and implementation

Before changes, **62 tests passed in 76.94 s**. Existing staged/unstaged work was inspected
and preserved. No Git author identity was invented; the index remains unchanged.

New modules: `planning.py` (shared contexts/proposals, reachable access paths, separators,
bounded candidates and interpretable scoring), `planner_oracles.py` (common replay cache,
exchangeable native/custom policies), `benchmark_targets.py`, `benchmark.py`,
`benchmark_summary.py`, `benchmark_audit.py`. Existing `learning.py` accepts optional
oracle/SUL factories and snapshot hooks while preserving M3 defaults. Existing M3
`refinement.py` and CLI support `--strategy cost-aware` through the same real differential,
shrinking, relearning, regression and standalone export pipeline.

Additional files: `tests/test_planning.py`; `scripts/run_m4_benchmark.py`,
`profile_m4_recording.py`, `reproduce_m4_cells.py`; development/pilot/confirmatory manifests;
M4 protocol/results documentation and README/project-state updates. No new dependency,
frontend, symbolic automaton, typed-amount inference, paid API or publication was added.

Four baselines, one proposal and three real component ablations were executed. L*,
counterexample processing, physical oracle, cache, reset, recording and model policies are
common. Unrestricted information gain and hypothesis committees are not claimed.

## Actual verification

| Check | Result / evidence |
|---|---|
| Complete final suite | **82 passed, 0 failed in 221.89 s**; `evidence/m4-pytest.txt` |
| Existing M0–M3 regression tests | Included, assertions retained; Windows timeout/cleanup fixes not weakened |
| Planner development tests | 17 passed in the earlier focused integration run; final 20 M4 cases included above |
| Lint | PASS; `evidence/m4-ruff.txt` |
| Formatting | PASS, 36 files already formatted; `evidence/m4-format.txt` |
| Static type checking | No checker configured; no type-check pass claimed |
| Primary benchmark | 120/120 cells completed; zero failed cells; no recovered/aborted primary cells |
| Evidence audit | PASS; 480 scores recomputed, SQL action/reset counts and reference outputs reconciled |
| Fairness | Identical contract/target fingerprints and evaluation hashes per pair; isolated DB/process/cache state |
| Leakage | No full-word overlap; model snapshots not backdated; training receives projected limits, not evaluation data |
| Reproducibility | Six representative cells matched from a non-editable installed package |
| Resume | Completed matrix resumed without rerunning cells; changed source/manifest identities reject resume |
| Negative paths | Tests cover physical-prefix cost, nondeterminism, budget exhaustion, interrupted evidence and failed/unreached thresholds |
| M3 integration | Real cost-aware differential counterexample discovery, AALpy refinement, export and regression replay test passed |

The primary SQL audit records 239,861 training actions / 42,066 resets and validates 10
distinct oracle programs. References cost 33,780 actions / 1,200 resets separately.
The original pilot's negative result, audit and source snapshot remain preserved; the
seed-separation amendment and fresh confirmatory seeds are explicitly documented. No
failed result or unreached threshold is removed to improve aggregates.

## Commands executed

From the enclosing workspace, using the existing development environment:

```powershell
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m4-baseline-tests
```

Primary commands (and the actual final full-suite command):

```powershell
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/profile_m4_recording.py --out outputs/blackbox-twin/evidence/m4-profile
work/.venv/Scripts/bbt.exe benchmark run --manifest outputs/blackbox-twin/benchmarks/manifests/m4-pilot.json --out outputs/blackbox-twin/evidence/m4-pilot
work/.venv/Scripts/bbt.exe benchmark run --manifest outputs/blackbox-twin/benchmarks/manifests/m4-confirmatory.json --out outputs/blackbox-twin/evidence/m4-confirmatory
work/.venv/Scripts/bbt.exe benchmark run --manifest outputs/blackbox-twin/benchmarks/manifests/m4-confirmatory.json --out outputs/blackbox-twin/evidence/m4-confirmatory --resume
work/.venv/Scripts/bbt.exe benchmark audit --out outputs/blackbox-twin/evidence/m4-confirmatory
uv pip install --offline --python work/clean-venv/Scripts/python.exe --reinstall-package blackbox-twin outputs/blackbox-twin
work/clean-venv/Scripts/python.exe outputs/blackbox-twin/scripts/reproduce_m4_cells.py --suite outputs/blackbox-twin/evidence/m4-confirmatory --out outputs/blackbox-twin/evidence/m4-reproduction
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m4-final-tests
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
```

The development seed-11 24-cell/500-action pilot was also run at `work/m4-development`.
Its code predates the final native-tail/cache-stat/source-guard refinements; it is development
evidence, not part of confirmatory statistics. Intermediate lint line-length findings were
fixed before freezing the relevant source. No failed automated test was hidden by weakening
an assertion. Offline installation used workspace-owned cache/temp directories; no new paid
service or runtime dependency was introduced.

## Adversarial conclusions and limitations

The proposal is an explicit scoring/pool modification, not a renamed native oracle. It
does not access generated tables, private state or evaluator references while learning.
Source fingerprints are taken by the launcher for provenance; they are not planner inputs.
An actual parent-side file guard test blocks hidden target/evaluator reads in training.
This is architectural separation, not an adversarial OS sandbox.

All membership, search, refinement and reset calls needed by this comparative track are
counted. Evaluation is separate. All strategies share cache policy; replayed prefixes cost
their full physical length. Benchmark shrink/regression phases are zero for every method,
not moved into excluded categories. Their full M3 integration remains separately tested.
Some native tests can be longer because access paths and separators augment random tails;
this genuine policy difference and all replay costs are explicit.

The full proposal loses or ties every native-baseline AULC pair; its two deep delayed
failures were confirmed by actual post-hoc original/twin probes. Coverage and separator
ablations give identical measured curves; added complexity has no demonstrated fidelity
value. Cost removal is mixed and sometimes improves performance. Runtime including overhead
does not rescue the hypothesis. These are negative results, not engineering failure by
themselves.

Remaining bounds: 3 small families, 5 seeds per family, repeated workflow program, coarse
query checkpoints, parsed JSON comparison, and Windows/Python 3.12 only. No population-level
significance, exact continuous threshold cost, universal equivalence or M6-level benchmark
claim is made. Timings are fixed-order local observations. Six cells, not the whole matrix,
were independently installed/reproduced. Package dependencies are pinned and recorded in
`evidence/m4-environment.json`; the resume digest checks project code/manifest, not arbitrary
external dependency modifications.

Resume is supported across completed cells and interrupted training-cell attempts with a
fresh learner/cache; it does not resume an in-memory AALpy table. Interruption during target
or evaluator-reference generation is not a verified recovery path; use a fresh output and
preserve/audit partial data rather than assuming its costs are complete. Power loss can
invalidate WAL NORMAL durability. Pilot manifests are fixed protocols, not a validated
arbitrary configuration/plugin system. These noncritical bounds motivate the limited
engineering verdict.

Next: reconsider this ranker using native policies as the reference. Do not tune on the now
observed evaluation seeds or begin M5 automatically. See `PROJECT_STATE.md` for continuation.
