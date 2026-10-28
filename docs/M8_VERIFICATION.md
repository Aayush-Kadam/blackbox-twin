# M8 verdict — NOT READY for public release

2026-10-28. The hardened Windows implementation is ready for continued local technical
review. Public release remains blocked by project licensing, attribution closure,
unverified physical link/junction boundaries and incomplete fresh frontend installation.
These are explicit gates, not an aggregate PASS. Linux is **NOT VERIFIED**.

## Verification matrix

| Check | Result | Evidence / limits |
|---|---|---|
| Pre-change diagnostic baseline | 154 passed, one warning; 183.77 s | `work/m8-baseline-traced.txt`; original incomplete log preserved |
| Focused final security/workbench tests | 39 passed, 4 skipped, one warning; 5.73 s | `m8-focused-recovery-v2.txt` |
| Full Windows Python 3.12.10 | 180 passed, 4 skipped, one warning; 156.18 s | `m8-final-python312.txt` |
| Full Windows Python 3.11.16 | 180 passed, 4 skipped, three warnings; 160.28 s | `m8-final-python311.txt` |
| Frontend | 11 passed; production build and Prettier passed | `m8-final-*-direct.txt`; existing installed dependencies |
| Python lint / format | Passed; 83 Python files formatted | `m8-final-ruff-v4.txt`, `m8-final-format-v4.txt` |
| Dependency advisory closure | 33 queries completed; no listed advisories at final versions | `evidence/m8-dependencies-patched-build/`; dated lookup, not vulnerability-free claim |
| Fresh wheel build/install | Passed, non-editable | setuptools 84.1.0 build; isolated venv; declared dependency lock |
| Fresh full supported demonstration | Passed, 88.496 s | `clean-reproduction/reproduction.json`; data kit only |
| Two profiled demonstrations | Both completed and independently audited | 53.535 s / 54.691 s; original profiler immediate cleanup status FAIL, resolved in separate follow-up |
| Installed Python 3.11 workbench | Startup, real browser replay/typed/benchmark checks, stop verified | `evidence/m8-browser/`; owned server PID no longer running |
| Supplemental edge cases | Passed | Three outside/normalized paths, four encoded/platform API paths, synthetic aborted-job restart, environment key set; `edge-checks.json` |
| Fresh frontend installation | BLOCKED | pnpm symlink registration denied by Windows; failure retained, no system-policy change |
| Physical link/junction cases | SKIPPED: 4 per Python suite | OS denied owned link creation; NOT passed, blocking broader filesystem-security signoff |
| Linux | NOT VERIFIED | Recovered WSL access denial / unavailable Docker Linux engine; no bypass attempted |
| CI | Prepared, NOT EXECUTED | Windows/Linux 3.11/3.12 plus frontend; no push authorized |

Final logs named above are copied into `evidence/m8-verification/logs/`; workspace `work/`
retains original logs, including failures and incomplete commands. Python suites are two
interpreter runs of the same 184 collected tests, not 360 independent behavioral cases.
Warnings: HTTPX TestClient deprecation on both interpreters; two AALpy invalid escape
DeprecationWarnings on 3.11. No warning filter or timeout weakening was applied.

## Implemented security changes

Current changes: resolved root containment for evidence and exports, fixture executable
containment, an explicit oracle subprocess environment allowlist, persistent repeated-demo
admission limits, bounded storage traversal, strict Host/method/origin checks, actual body
byte/deadline limits, malformed/nested JSON rejection, conservative response headers and
sanitized API errors. See `M8_THREAT_MODEL.md` for severity and residuals and
`M8_DEPENDENCIES.md` for all seven original GHSA records and remediation.

Starlette 0.49.3 was affected by five GHSA records. It is now 1.10.0 with compatible
FastAPI 0.162.0. Expanding the audit to the build backend found two more GHSA records
affecting setuptools 80.9.0; the build pin and installed backend are now 84.1.0.
Original affected audits and historical locks remain preserved. No listed advisory
remains for final queried versions; future discoveries and platform-specific gaps remain.

The four skipped physical cases cover historical folder escape, nested loop escape,
allowed fixture name linked outside, and linked output storage. Resolve-based guards
and supplementary logical/API checks passed, but physical OS behavior is not established.
Release signoff must retain that gap until an authorized host executes those cases.
This workbench still executes trusted owned programs with same-user filesystem/network
access, and resource limits are admission checks rather than OS containment.

## Compatibility and independent installation

Both interpreters passed import and CLI module smoke checks, the core/full suite and
standalone generated-twin tests. Python 3.11 additionally served the real browser smoke
session; Python 3.12 served two real profiled experiments from the independent install.
The fresh 3.12 wheel installation used only the declared runtime/test transport lock,
not developer imports or an editable package. Its module path was inside the new venv.
The 29-file / 5,831,724-byte data kit has a manifest checked before reproduction; it is
a declared curated subset, not the entire M6 campaign. Runtime does not consult installer
caches, credentials or undeclared original checkout paths. See `DEVELOPER_GUIDE.md`.

Fresh supported run: 1 → 5 states, 10 → 5 action witness, 35/35 regressions;
73/100 → 100/100 exact frozen traces and 1967/1996 → 1996/1996 outputs. Physical costs:
original training 1855 actions / 288 resets; original paired evaluation 3992 / 200;
twin training 1043 / 174, twin evaluation 3992 / 200; isolated twin replay 5 / 1.
All three M8 demonstrations match these costs and scores. These are demonstrations,
not new M6 benchmark cells or proof of general equivalence. The fresh installation also
reproduced all four typed support labels and a zero-query unsupported inventory adapter.

## Windows resource measurements

Native Toolhelp ancestry, GetProcessMemoryInfo and GetProcessTimes sampled the owned
installed workbench process tree at a target 50 ms interval. Two sequential demos:

| Metric | Measurement |
|---|---:|
| Samples / final sample elapsed | 1744 / 112.611 s |
| Peak sampled summed working set | 102,019,072 bytes (97.293 MiB) |
| Peak sampled summed private commit | 64,585,728 bytes (61.594 MiB) |
| Median idle summed working set | 62,484,480 bytes (59.590 MiB) |
| Observed aggregate CPU | 89.969 CPU seconds, about 0.80 core averaged over sampled elapsed time |
| Peak sampled process count | 6 |
| HTTP readiness / signal shutdown | 2.737 s / 0.258 s |
| Experiment artifact disk | 7,128,293 bytes across two runs |
| Remaining profiler temporary directories / bytes | 0 / 0 |

Evidence: `evidence/m8-profile/{profile,samples,cleanup-followup}.json`, server log and
two persisted experiments. Summed working sets can double-count shared pages; private
commit is not physical RAM. Sampling misses short peaks/children and final CPU increments.
Browser renderer, unrelated system processes and laptop-wide memory pressure are excluded.
The observed workload is small relative to the laptop's stated 16 GB, but no 16 GB-wide
capacity guarantee, maximum RAM cap or concurrency scaling result is established.

The original profiler returned FAIL because its immediate post-shutdown counter lookup
still identified two PIDs. Later native checks found neither running and the server log
shows completed shutdown. The helper now excludes nonzero exit timestamps and permits
a two-second drain; a controlled retained exited-process check passed. No expensive demo
was rerun or old result overwritten. Treat numeric resource measurements as collected
evidence and cleanup as separately verified follow-up, not a retroactive profiler PASS.

## Preserved scientific evidence

Read-only audits passed for M3, M5, M5.1, historical M7 and all three fresh M8 runs.
M6 verification reconciled all 216 cells / 324 points and 582 integrity folders, retained
214,815 training actions and all frozen source hashes. Current `oracle.py` differs only
as an explicit M8 hardening change; the historical source snapshot remains intact.
Four current M7 modules differ from the pre-M8 snapshot: m7_data, m7_demo, oracle,
workbench. New boundary/limit modules are separately added. Archived M7 hash validation
uses the preserved baseline snapshot when current security code legitimately differs.

M4's 120-cell negative-result report remains preserved; full-suite M4 regression tests
passed. Its forensic writer was deliberately not rerun because it writes into historical
evidence. No fresh M4 campaign was conducted. No M6 campaign was rerun. Inventory remains
unsupported; query-efficiency superiority is unproven; the custom ranker underperformed.
See the original benchmark protocol, failure analysis and prior-art attribution.

## Failures and limitations retained

The first old baseline was incomplete; the diagnostic baseline completed. Recovery's
first focused command encountered unwritable system temporary storage, and its newly
added deep-JSON test exposed reliance on the interpreter recursion limit. Workspace-owned
temp paths resolved the environmental issue; the boundary now enforces an explicit depth
ceiling. Focused checks and both full suites passed afterward. New tests were corrected
to use an explicit unexpected content type. No preexisting assertions were lowered.
An earlier new large-body test ID exceeded Windows environment size; shortened IDs retain
the same payload/assertions. Its raw log is retained locally and not copied to the review
bundle because an environment repr appears there; a redacted diagnostic copy is preserved.

Initial 3.11 dependency downloads timed out; the recovery install completed. One advisory
attempt failed DNS; its UNKNOWN result remains alongside later completed queries. The
pnpm wrapper and fresh install hit Windows symlink denial; direct Node test/build/format
commands succeeded with existing dependencies. No access restriction was bypassed.
The supplemental edge script initially chose an evidence output directory and was correctly
rejected by the historical-output guard; its second run used a fresh workspace path.
The evidence finalizer initially compared a lowercase SHA256 string to an uppercase
expected string and failed. Correcting only comparison case passed; the Git index itself
was unchanged. Wheel inspection found 47 entries, no bytecode/tests/evidence/private
workspace literal, and all four bundled asset hashes matched the current production build.

## Release recommendation

**NOT READY** for a public release; continue local independent review. Close the unchecked
items in `RELEASE_CHECKLIST.md`: owner licensing, upstream attribution texts, actual
physical link/junction tests and fresh frontend install. Keep Linux unverified until real
execution; prepared CI is not a green run. Consider Apache-2.0's explicit patent terms or
MIT's shorter permissive terms as described in `LICENSING.md`; no license has been selected.
The release-summary draft is local and unpublished.

Servers and recorded owned child PIDs were stopped; native listener enumeration showed
no listener on 8765/8766. The browser server's Ctrl+C ended the owned process; a graceful
application-shutdown log was not captured for that PTY session, so only actual exit is
claimed there. The profiling server did log graceful application shutdown. No system-wide
process-absence claim is made. Git index SHA256 remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
No staging, commit, push, publication, deployment, release or visibility change occurred.
