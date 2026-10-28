# M5 verification — 2026-10-27

**M5 — PASS WITH LIMITATIONS.** The essential typed reconstruction, real boundary probes,
restricted guard/update fitting, standalone generation and automatic differential
refinement work. Uniform generalization and robust boundary identification do not.
M4's performance hypothesis remains NOT SUPPORTED. No publishing, pushing or M6 campaign.

## Subphase gates

| Gate | Result | Evidence |
|---|---|---|
| M5.0 contract freeze | PASS | `M5_WALLET_CONTRACT.md`, versioned manifest, `evidence/m5-contract-freeze.json` saved before inference |
| M5.1 typed infrastructure | PASS | Existing Action/Session/Recorder/cache representation; strict int/bool/enum/optional schemas; previous tests unchanged |
| M5.2 adaptive boundaries | PASS in bounded scope | Real contrasting probes, model disagreement/adjacent cuts, physical limits, fixed-grid comparison; no efficiency-win claim |
| M5.3 guarded model/twin | PASS WITH LIMITATIONS | Version 2; learned state relations and add/subtract updates; A handles held-out amount 2 in every evaluator context; B has unresolved ambiguity |
| M5.4 differential refinement | PASS | Actual `deposit(4)` / `deposit(3)` CEs; M3 ddmin plus typed shrinking; final replays agree; 163/163 and 127/127 regressions |
| M5.5 evaluation/hardening | PASS WITH LIMITATIONS | Frozen held-out words/values, exhaustive contextual evaluator, leakage audit, clean-install/isolated reproduction; only two evaluation configurations |

These limits are material: B adaptive unseen-sequence fidelity is 19/30, below fixed
grid's 29/30, despite higher exhaustive contextual agreement. The fitter chooses one
consistent regularized guard set and does not abstain for every possible untested cut.
No final evaluator observations were fed back to repair this result. M5 is not a uniform
correctness, efficiency, arbitrary-input or general register-synthesis result.

## Actual tests and audits

Before substantial implementation, **88 tests passed, 0 failed in 129.58 s**:
`evidence/m5-baseline-pytest.txt`. Intermediate full suite: 109 passed in 138.60 s,
preserved at `m5-intermediate-109-pytest.txt`. After adding explicit nonconvex-guard rejection
and state-dependent shrinking cases, the **final complete suite passed 111 tests, zero
failed in 140.70 s**: `evidence/m5-pytest.txt`. Focused M5 file: 23 passed in 6.44 s.
No older assertion, timeout or Windows cleanup behavior was weakened.

Tests cover strict integer validation including bool/float/null rejection; Boolean, enum,
optional/nullability schemas; canonical typed identities and versioned keys; physical
cache budgets; exact JSON differences; state-dependent boundary/output behavior; model
serialization and rejected unknown expressions; observation contradictions; unrepresentable
nonconvex guards; explicit unsupported regions/updates and unknown-state propagation;
standalone generation; held-out value separation; real parent-side forbidden-file access
guards around training; automatic CE replay/regression; and semantic argument shrinking
that retains a necessary deposit before a successful withdrawal failure.

Ruff lint **PASS** (`evidence/m5-ruff.txt`), formatting **PASS, 50 files**
(`evidence/m5-format.txt`). No static type checker is configured or claimed.

`scripts/audit_m5.py` reports **PASS** at `evidence/m5-audit.json`:

- Frozen contract/fixture/config hashes and frozen inference source match their receipts.
- Four independent training cells reconcile to SQLite: **6,412 original actions / 2,157 resets**.
- Shared original reference acquisition is separate: **4,055 / 858**. Primary original
  total including evaluation: **10,467 / 3,015**. Separate twin calls: **9,233 / 2,030**.
- Every phase sum equals total physical actions. All cells stay inside 5,000/1,000 caps.
- Reserved values are absent from all physical training requests; no held-out full-word
  overlaps; inputs were frozen before training started.
- Initial adaptive/fixed-grid rules and states match within each pair. Both methods have
  identical underlying learner, initial phase and state-cover behavior.
- Every final rule fits its recorded observations; standalone predictions equal serialized
  model predictions for all 470/388 evaluator cases.
- All exact trace/output/unsupported numerators, acceptance guard precision/recall and
  complete boundary sets are recomputed from independently executed SQLite traces.
- All saved minimized counterexamples replay with agreement and all contextual regressions pass.

M2 and M3 immutable evidence audits were reexecuted successfully:
`evidence/m5-m2-audit.json`, `m5-m3-audit.json`. M4's 120-cell / 480-checkpoint audit was
reexecuted with its preserved frozen source: `m5-m4-frozen-audit.json`. Historical verdicts,
counts, models, staged entries and negative findings were preserved. The Git index tree
remains `9d804578899a21849533231252b1a2fbb7e23059`; no identity, commit or remote was invented.

## Source preservation and reproduction

Primary `protocol.json` records every then-current package source hash, alongside the
contract freeze and input-freeze time. Source copies are preserved at
`evidence/m5-primary/source-snapshot/blackbox_twin/`. One long diagnostic string line was
wrapped after the run for lint. `evidence/m5-source-format-amendment.json` records before/
after hashes and confirms identical Python AST; no algorithm or string value changed.
The audit verifies frozen copies, not falsely substituted current hashes. The installed
reproduction uses the formatted equivalent code and matches the measured model/costs.

Offline non-editable installation succeeded (`evidence/m5-install.txt`). One complete
adaptive A training cell was repeated using `work/clean-venv` installed code. It reproduced
**2,112 actions / 666 resets**, identical CE, rules and observed states. The generated
twin was copied into an otherwise empty folder and run with `python -I -S -u`; its only
file was the generated interpreter. All **470 cases / 2,294 actions / 470 resets** matched
the original references exactly. No target source, database or BBT package was needed
for twin execution. Receipt: `evidence/m5-reproduction/summary.json`.
This is one installed learning cell, not an independent repetition of all four cells.

No dependency was added. Bounded enumeration of the tiny candidate grammar suffices;
Z3 would not resolve observational uncertainty without new target observations.
Integer arithmetic is exact. All wallet/configuration/evaluation code remains local.

## Commands actually executed

From the enclosing workspace, TEMP/TMP were set to its `work` directory for tests and
UV_CACHE_DIR to `work/uv-cache` for offline installation. Use fresh output/test directories.

```powershell
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m5-baseline-tests
work/.venv/Scripts/bbt.exe typed --development --out work/m5-development
work/.venv/Scripts/bbt.exe typed --out outputs/blackbox-twin/evidence/m5-primary
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m5.py --suite outputs/blackbox-twin/evidence/m5-primary
uv pip install --offline --python work/clean-venv/Scripts/python.exe --reinstall-package blackbox-twin outputs/blackbox-twin
work/clean-venv/Scripts/python.exe outputs/blackbox-twin/scripts/reproduce_m5.py --suite outputs/blackbox-twin/evidence/m5-primary --out outputs/blackbox-twin/evidence/m5-reproduction
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/m5-final-full-tests
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
```

The primary commands above already ran and their output directories must not be reused.
For a new installed-package demo, pass `--project` pointing to the saved project root,
because evaluator fixtures/manifests are source artifacts rather than installed package
resources. `bbt learn` still recommends StatePrefix; its eight existing strategies remain.
`bbt typed` runs this specific two-arm M5 protocol, not a general arbitrary-schema learner.

## Remaining gates and next action

Do **not** start a broader M6 performance campaign yet. First specify a bounded robustness
follow-up: preserve ranges of feasible boundary cuts rather than only representative
cuts, define when disagreement forces unsupported, and design independent identifying
experiments where some values must remain withheld. Freeze the revised support policy
before new configurations. This is a recommendation, not implemented work or authorization
for optimization. Also expand reset-state validation, schema breadth in actual targets,
hidden-state sufficiency tests and state-dependent CE cases before claiming broad support.

Symbolic references, hidden registers, nonconvex/disjunctive business classes, arbitrary
output expressions and infinite domains remain unsupported. The successful observable
wallet slice and negative B result are both retained for the next decision.
