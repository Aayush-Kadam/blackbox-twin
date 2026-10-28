# M8 recovery inventory — 2026-10-28

Recovered from saved files before resuming. Earlier logs remain intact under workspace
`work/`; historical M0–M7 evidence is not replaced. Git index SHA256 remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.

| Component | Completed at recovery | Pending | Evidence |
|---|---|---|---|
| Baseline tests | 154 passed, one warning, 183.77 s | Final suite after fixes | `work/m8-baseline-traced.txt`; incomplete `m8-baseline-python.txt` retained |
| Dependency updates | FastAPI 0.162.0 / Starlette 1.10.0 installed; prior lookup completed | Normalized full closure and build dependency lookup | `requirements-m8-lock.txt`, `evidence/m8-dependencies-*` |
| Security fixes | Path containment, environment allowlist, admission limits, bounded HTTP middleware applied | Final regression and inspection | `tests/test_m8_security.py`; 31 passed / 4 skipped combined with M7 tests |
| Link/junction checks | Four physical cases attempted | OS denied creation; remain skipped | `work/m8-security-tests-final.txt` |
| Python-version checks | 3.12 baseline; 3.11.16 interpreter starts | 3.11 dependencies timed out; package/suite unverified | `work/m8-311-locked-install.txt` |
| Linux checks | WSL access denied; no Docker Linux engine | NOT VERIFIED | Previous session platform probes |
| Frontend checks | 11 tests and production build passed | Final verification / clean install | `work/m8-baseline-frontend.txt`, `m8-baseline-build.txt` |
| Performance profiling | Native Windows profiler written | Execute bounded representative run(s) | `scripts/profile_m8.py` |
| Clean-install reproduction | M7 reproduction retained | M8 wheel, declared data kit, fresh environment | `scripts/reproduce_m7.py`, M7 report |
| Release documentation | Historical reports retained | M8 verdict, security, installation and licensing | `docs/PROJECT_STATE.md` still held M7 state at recovery |

No prior shell session is assumed alive after recovery. Every new verification command
gets a new log. The newest advisory attempt failed DNS and is explicitly UNKNOWN in
`evidence/m8-dependencies-recovery/audit.json`; it does not supersede successful older
lookups or establish a clean final result.
