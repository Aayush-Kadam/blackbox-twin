# Verification — 2026-10-27

Historical M0–M2 report below. M3 is now closed as **PASS** within its declared scope;
see [M3_VERIFICATION.md](M3_VERIFICATION.md) for 62 passing tests, repairs and final evidence.

M0, M1 and M2: **PASS WITH LIMITATIONS** for the declared owned-fixture finite-alphabet
scope. At this historical checkpoint, M3 had only its standalone export prerequisite;
its later completion is documented separately. The project remains not release-ready.

| Executed check | Actual result | Evidence |
|---|---|---|
| Final pytest run | 24 passed in 48.56 seconds | `evidence/pytest.txt` |
| Ruff lint | All checks passed | `evidence/ruff.txt` |
| Ruff format | 14 files already formatted | `evidence/format.txt` |
| Installed CLI learning | 6 states; 2,004 actions; 368 resets; 1 L* round | `evidence/demo-training-v2/summary.json` |
| Learning physical-cost breakdown | 864 membership actions + 1,128 search actions + 12 reset-probe actions | Same summary and event DB |
| AALpy cache | 6 logical query cache hits | `aalpy_statistics.cache_saved`; not physical savings |
| Separate held-out evaluation | 100/100 exact traces; 1,492/1,492 steps; 1,036/1,036 target-error outputs | `evidence/demo-heldout/evaluation.json` |
| Evidence audit | Counts match SQL; model hash matches evaluation; zero full-sequence overlap | `evidence/audit.json` |
| Tiny model recovery | 2 learned states; all 62 words of lengths 1–5 agree with evaluator-only truth | `tests/test_adversarial.py::test_tiny_two_state_recovery` |
| Independent twin | Runs from an otherwise empty directory in isolated Python; observed unsupported handling | `tests/test_core.py::test_standalone_twin` |
| Non-editable installation | Fresh environment; package build/install succeeded offline from cached dependencies; inspect/replay succeeded | `evidence/clean-install-replay.sqlite` |
| CI | Configuration created; not executed remotely | `.github/workflows/ci.yml` |
| Local commit | Blocked by missing Git author identity; no identity configured | No commits; staged files retained |

## Actual commands

Commands below ran from the enclosing workspace. The project environment is in
`work/.venv`; all deliverables are in `outputs/blackbox-twin`.

```powershell
python --version
node --version
uv pip install --python work/.venv/Scripts/python.exe aalpy pydantic pytest ruff
uv pip install --python work/.venv/Scripts/python.exe -e 'outputs/blackbox-twin[dev]'
work/.venv/Scripts/bbt.exe learn --target outputs/blackbox-twin/examples/order_processing/target.json --out outputs/blackbox-twin/evidence/demo-training-v2 --budget 10000
work/.venv/Scripts/bbt.exe evaluate --target outputs/blackbox-twin/examples/order_processing/target.json --model outputs/blackbox-twin/evidence/demo-training-v2/model.json --training-db outputs/blackbox-twin/evidence/demo-training-v2/observations.sqlite --out outputs/blackbox-twin/evidence/demo-heldout --count 100 --seed 2027
work/.venv/Scripts/bbt.exe replay --target outputs/blackbox-twin/examples/order_processing/target.json --out outputs/blackbox-twin/evidence/demo-replay.sqlite create capture authorize capture status
work/.venv/Scripts/bbt.exe export outputs/blackbox-twin/evidence/demo-training-v2/observations.sqlite outputs/blackbox-twin/evidence/demo-training-v2/events.jsonl
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=work/pytest-verified
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/fixtures outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/fixtures outputs/blackbox-twin/scripts
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_evidence.py
uv venv --python '<LOCAL_REVIEW_PATH>' work/clean-venv
uv pip install --offline --python work/clean-venv/Scripts/python.exe outputs/blackbox-twin
work/clean-venv/Scripts/bbt.exe inspect outputs/blackbox-twin/examples/order_processing/target.json
work/clean-venv/Scripts/bbt.exe replay --target outputs/blackbox-twin/examples/order_processing/target.json --out outputs/blackbox-twin/evidence/clean-install-replay.sqlite create capture authorize capture status
git -C outputs/blackbox-twin diff --cached --check
```

Install/test commands used workspace-owned `TEMP`, `TMP` and `UV_CACHE_DIR` where needed.
The initial dependency download required approved network access after restricted DNS failed.
Pinned observed versions are in `requirements-lock.txt`. This is a version snapshot, not a
hash-locked cross-platform resolver output.

## Failures retained and corrections

- `python -m venv` created the interpreter but ensurepip failed. uv installed dependencies
  into that environment instead. A default uv cache path was denied; using a workspace
  cache resolved it. A later freeze attempt repeated the default-cache issue and was
  stopped; installed package metadata produced the version snapshot instead.
- First test run: **7 failed, 9 passed**. The SQLite event insertion had seven placeholders
  for six columns. Corrected; subsequent suite: **16 passed**.
- Initial installed CLI run exited 1 on system-temp cleanup after model generation.
  Artifacts remain under `evidence/demo-training/` with `FAILURE.md`. Workspace-owned
  process directories fixed the issue; the fresh `demo-training-v2` run completed.
- Expanded suite: **1 failed, 20 passed**. A test expected a model after an 800-action stop,
  but the first complete observation table needs 864 actions for this configuration.
  The test now verifies both no checkpoint before completion (800) and preservation after
  completion (1,000). Subsequent run: **22 passed**.
- Added injected cleanup and startup failures; final suite: **24 passed**.
- A diagnostic one-line SQL command was rejected by PowerShell quoting before running;
  the durable audit script avoids shell-embedded SQL and passed.
- AALpy emits two upstream invalid-escape SyntaxWarnings on initial Python 3.12 import.
  They did not prevent tests or installation.
- Memory inventory via CIM was denied. Python 3.12.10, Node 24.22.1 and approximately
  65 GB free disk were observed; installed physical memory was not verified.
- A local Git commit was attempted and rejected for missing author identity. No global
  or repository identity was fabricated. No remote was configured or published.

## Adversarial conclusions

The learner receives a finite interaction contract and observed outputs, not target
implementation state. Source imports are checked, but same-user filesystem confidentiality
is not enforced. The twin composes transitions and needs neither oracle nor DB. However,
the informative status operation makes the order fixture easy, and one L* round found the
model: this run does **not** demonstrate counterexample-driven refinement. No comparison
with memoization, passive learning or a custom planner has been performed. Those claims
remain unavailable. Reset probes and finite samples do not prove target determinism or
equivalence. See `LIMITATIONS.md` for the residual security and methodological risks.

Next: implement M3 using a delayed-distinguishing fixture that produces a real model
disagreement, minimize it by replay, persist it, feed it into the learner and re-evaluate
with a new frozen hold-out set. Never reuse this held-out set for tuning a reported run.
