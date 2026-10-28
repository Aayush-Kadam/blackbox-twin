# M6 verification — 2026-10-27

**PASS WITH LIMITATIONS.** All checks below were executed after the frozen campaign.
No package source was changed after freezing confirmation. No tests or timeouts were
weakened. No configured type checker exists, so no type-check pass is claimed.

## Development pilot

The nine-cell pilot tested one easy finite target (generation seed 71), one separate
wallet configuration and one inventory configuration. The actual learner seed was 15137,
training-oracle stream seed 27109, evaluation seeds 95131 / 95168 / 95205. Only the first
learner/training seeds in the pilot manifest were executed; unused listed seeds are not
extra runs. Total physical training cost was 5,241 actions / 1,825 resets.

| Track / method | Actions | Overall trace fidelity |
|---|---:|---:|
| A / StatePrefix | 250 | 1 |
| A / Random W | 250 | 1 |
| A / random | 249 | 1 |
| B / fixed-grid | 1091 | .89860 |
| B / adaptive | 1500 | .93357 |
| B / hardened | 1401 | .93007 |
| C / concrete fixed-grid | 500 | 0 |
| C / adaptive | 0 | 0, compatibility rejection |
| C / hardened | 0 | 0, compatibility rejection |

The adaptive pilot's completed label was incorrect after a regression budget stop.
It was fixed before confirmation; the affected-only recheck spent another 1,500 actions /
499 resets and correctly recorded action_budget with 45/45 completed regressions. Original
pilot evidence, source snapshot and flawed status remain preserved; its data are development,
not confirmation. Inventory concrete learning produced no complete hypothesis at 500.

## Automated checks

- Full suite: **141 passed in 171.15 seconds** on Windows / Python 3.12.10.
  The previous suite had 130 tests; eleven M6 tests cover independent RNG streams,
  seed validation, integrity/resume, interrupted-attempt preservation, denominators,
  target-weighted aggregation, zero-query compatibility, bounded/file-isolated training,
  historical fixture preservation, executable unknown-state/reset behavior and small
  end-to-end campaign resume. A test can cover multiple checks.
- Ruff lint: all package sources, tests and scripts passed.
- Ruff formatting check: **64 files already formatted**.
- Existing CLI help executes successfully.
- Git whitespace check passed; ordinary LF/CRLF conversion notices remain.
- The index SHA256 remained
  `7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
  Existing staged work was not changed; nothing was committed, pushed or published.

Original failing baseline logs remain in `evidence/m6-recovery/`. Two earlier full runs
each returned 129 passes / one Windows failure, respectively cleanup and process termination.
Recovery focused checks passed 3 tests in 4.75 seconds. The final passing suite includes
those unchanged tests. Passing a later suite does not erase those earlier failures.

## Physical and semantic audits

`scripts/audit_m6.py` passed for 216 cells / 324 points. It verifies source/resource hashes,
target/input freeze order, historical rare fixture bytes, completed artifact integrity,
physical action/reset and phase totals, independent reference outputs, measured standalone
outputs versus serialized models, category metric numerators/denominators, bounded support
recompilation, finite-product checks and the predeclared success criterion. Training excludes
reserved evaluation values. All original training/reference attempt actions reconcile;
there are no partial-attempt costs. `audit.json` records separate twin costs.

`scripts/audit_m6_support.py` additionally passed: **24 hardened models / 1,952 observations**
reconciled to physical experiment/state/action/output rows; all completed training regressions
passed. The first audit rebuilt all 24 models from observations/version spaces exactly.

`scripts/analyze_m6.py` independently recounts guard TP/FP/FN/TN and checks saved guard
precision, recall and population size. It creates target-weighted stratum summaries and
`metrics.csv`; no rows are removed on performance grounds. Full-word overlap accounting
reports 1,488 scored-point intersections, entirely exhaustive diagnostics, zero in frozen
random/challenge strata. Overlap is disclosed rather than regenerated away.

## Non-editable installation and independent twins

The package was rebuilt offline and reinstalled non-editably into the existing isolated
`work/clean-venv` verification environment, with pinned AALpy 2.0.0 / Pydantic 2.14.1.
Installation metadata has no editable flag. This is an isolated package-install check,
not a fresh operating-system test. The installer fell back from hardlinks to file copies;
installation still succeeded.

`scripts/reproduce_m6.py` ran using that installed package, asserted all frozen package
hashes, and independently retrained one representative from every executable class.

| Target / method | Status | Original actions | Resets | Isolated twin requests |
|---|---|---:|---:|---:|
| A-easy-0 / StatePrefix | action_budget | 1000 | 88 | 1581 |
| B-wallet-0 / hardened | completed | 1217 | 460 | 2162 |
| C-inventory-0 / concrete fixed-grid | action_budget | 1500 | 498 | 2663 |

All three matched the original status, physical actions/resets and predictions across
their complete frozen evaluation sets. Each newly generated twin ran as a standalone
`python -I -S` process without package imports, including reset requests: **6,406 requests**
matched the saved prediction policy. This includes inventory refusals and does not mean
6,406 correct original-target responses. Reproduction added 3,717 original training actions
and 1,046 resets, separately from confirmation. Numerical timing is not expected to match.

Evidence: `evidence/m6-clean-reproduction/verification.json` and individual new models,
twins and observation databases. All 324 main campaign points were also evaluated through
independent generated-twin processes before being scored.

## Reproduction commands

From the workspace root, using the existing project environment:

```powershell
$env:TEMP="$PWD/work"
$env:TMP="$PWD/work"
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m6.py --out outputs/blackbox-twin/evidence/m6-confirmatory-v1
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m6_support.py --root outputs/blackbox-twin/evidence/m6-confirmatory-v1
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/analyze_m6.py --root outputs/blackbox-twin/evidence/m6-confirmatory-v1
```

Non-editable install and the executed representative reproduction:

```powershell
$env:UV_CACHE_DIR="$PWD/work/uv-cache"
uv pip install --offline --python work/clean-venv/Scripts/python.exe --reinstall-package blackbox-twin outputs/blackbox-twin
work/clean-venv/Scripts/python.exe outputs/blackbox-twin/scripts/reproduce_m6.py --root outputs/blackbox-twin/evidence/m6-confirmatory-v1 --out outputs/blackbox-twin/evidence/m6-clean-reproduction
```

The reproduction output already exists and is intentionally not overwritten: use a fresh
folder for any separately authorized repetition. Completed confirmation should not be
rerun for nicer results. Resume only with the identical protocol/source, using:

```powershell
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/run_m6.py run --manifest outputs/blackbox-twin/benchmarks/manifests/m6-v1.json --out outputs/blackbox-twin/evidence/m6-confirmatory-v1 --resume
```

Fresh campaign execution uses a fresh output folder and the frozen manifest. Preparation
verifies all targets before training; resume reuses integrity-checked completed attempts.
Live AALpy table continuation is not supported. Changing source requires a new independently
identified protocol/run; it must not be presented as the original frozen confirmation.

## Authorization and review history

The exact blocked file was `src/blackbox_twin/m6_train.py`. The earlier review exhausted a
usage limit and made no safety determination; creation did not occur. The owner explicitly
authorized resubmitting that exact creation through normal file review. The reviewed patch
then succeeded. No alternate route was used and no authorization blocker remains.

Successful commands/logs are preserved in `evidence/m6-verification/`, plus the audit and
reproduction JSONs. Earlier pilot/baseline failures remain. During final checks one initial
Git command ran from the workspace parent (not a repository), failed harmlessly, and was
corrected to `git -C outputs/blackbox-twin`. Draft audit/report scripts had lint findings
that were corrected; the final complete lint/format checks passed. No new review rejected
an operation. No release, external service or M7 implementation was attempted.
