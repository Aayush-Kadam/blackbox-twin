> Historical M8.2 closure, 2026-10-28. M8.3 subsequently authorized public source visibility subject to final checks. Earlier authorization restrictions below remain as recorded.

# M8.2 — private release validation passed

2026-10-28. **READY FOR SEPARATE OWNER RELEASE REVIEW** within the documented local,
owned-fixture research scope. Public visibility, releases, hosting and deployment are
not authorized and were not enabled.

Private repository: https://github.com/Aayush-Kadam/blackbox-twin

Verified revision: `a6c8a1053fab3441586795b733b707a616e4f5b5`.
[Completed hosted workflow](https://github.com/Aayush-Kadam/blackbox-twin/actions/runs/40700717049):
all six jobs succeeded. These are executed results, not a prepared workflow claim.

| Hosted job | Python/frontend tests | Skips / failures | Python suite time | Independent package/demo |
|---|---:|---:|---:|---|
| Ubuntu, Python 3.11 | 189 passed | 0 / 0 | 40.52 s | PASS; 13.008 s |
| Ubuntu, Python 3.12 | 189 passed | 0 / 0 | 38.56 s | PASS; 13.710 s |
| Windows, Python 3.11 | 189 passed | 0 / 0 | 75.64 s | PASS; 22.673 s |
| Windows, Python 3.12 | 189 passed | 0 / 0 | 77.43 s | PASS; 28.335 s |
| Ubuntu frontend | 11 passed | 0 / 0 | — | Fresh frozen install, build and format PASS |
| Windows frontend | 11 passed | 0 / 0 | — | Fresh frozen install, build and format PASS |

Each Python suite emitted one existing Starlette/HTTPX TestClient deprecation warning.
The same 189 cases were run on four OS/interpreter combinations; they are not 756
independent research experiments. GitHub also reported action-runtime deprecation and
Ubuntu-image migration notices. No warning or assertion was suppressed.

## Ownership, licensing and authentication

The owner explicitly selected Apache-2.0, confirmed authority over original contributions
and compatible third-party use, and specified **Copyright 2026 Aayush Kadam**. The review
found no conflicting claim in original project modules or separate-permission exception.
Documented upstream copyright holders retain their own terms; none was relabelled as
original project ownership. LICENSE contains the unmodified official Apache-2.0 text
(SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`).
NOTICE and package metadata reflect the approved choice. The wheel's license expression,
LICENSE/NOTICE files and complete bundled MIT texts were independently inspected.

The authenticated GitHub account and repository owner were verified as Aayush-Kadam.
The repository name was available; it was created private and empty, rather than reusing
unexpected existing content. Git had no appropriately configured author identity, so
commits paused until the owner explicitly supplied the name and noreply email. That
email matched GitHub's displayed settings. Identity configuration is repository-local
only to the isolated release checkout. No global identity setting or credential value
was extracted, exposed or repurposed. Ordinary Git Credential Manager authentication
was used through the normal command-review path after the restricted shell helper failed.

## Physical filesystem evidence

All seven existing/new physical-link cases passed in every hosted Python job: historical
folder escape, nested loop escape, fixture executable escape, linked output storage,
broken output root, nested link chain and replacement before revalidation. The strict
CI flag converts unavailable link creation into failure, so these are actual physical
executions, not mocked substitutes or hidden skips.

The helper creates real symlinks and has a Windows junction fallback. Logs do not identify
which construction branch was used per case; this is not certification of every Windows
reparse-point kind. The laptop's creation restrictions were not changed. Concurrent
replacement during an open and OS-enforced hostile-code isolation remain outside the
verified trust model. Supplementary metadata checks remain separate from physical tests.

## Failures preserved and fixes validated

| Run / revision | Observed result | Resolution |
|---|---|---|
| 40696158699 / 2363c00 | Windows frontend tests/build passed but Prettier failed after checkout CRLF conversion. Windows 3.12: 188 passed / 1 failed. Windows 3.11 interrupted near job limit with 125 passed / 4 failed; remaining cases unexecuted. Ubuntu jobs passed. | Added scoped LF checkout policy; preserved evidence/input bytes. Investigated slow durable SQLite commits and wall-budget failures. |
| 40696970087 / 19f5456 | Both frontends and Ubuntu jobs passed. Windows 3.12 passed 189 and smoke; Windows 3.11 reached the unchanged job deadline with 121 passed / 3 failed and incomplete remainder. | Use workspace-owned temporary storage instead of profile-temp storage, retaining SQLite durability and all budgets. |
| 40699740758 / 772ed35 | GitHub rejected job-level runner context expressions; no jobs executed. | Move runner.temp expressions to supported step environment scope. |
| 40700121727 / 4b9966e | Python jobs: 78 passed / 111 fixture setup errors because work/ci-tests had no existing parent. Frontends passed. | Explicitly prepare the workspace parent; reproduce the initially empty layout locally. |
| 40700717049 / a6c8a10 | All six jobs succeeded, as detailed above. | Final verified revision. |

The Windows stacks showed event commits on the profile-temp volume; other failures
explicitly reported total-wall-clock budget exhaustion. Workspace-owned pytest storage
reduced the final Windows suite times to about 76–77 seconds. This operational improvement
does not establish an algorithmic query-efficiency advantage. No learning strategy,
fixture, evaluation sequence, scientific threshold, wall/action/reset budget, SQLite
durability setting or test expectation was relaxed. One assertion gained its existing
result as a failure diagnostic; its condition stayed identical. The 20-minute job limit
also stayed unchanged. No broad system policy or endpoint protection was changed.

The local evidence aggregator initially decoded UTF-8 job logs using Windows' default
code page; explicit UTF-8 decoding corrected that reporting-only failure. Original job
logs and failed run links remain preserved. No failed result was relabelled PASS.

## Package reproduction and scientific limits

All four final Python jobs built and independently installed a non-editable wheel into
a fresh environment and verified the declared data kit, supported full demo, isolated
standalone twin, four typed-support labels and unsupported inventory behavior.
The source module path was inside the new environment. Each supported demo retained
73/100 initial and 100/100 refined frozen traces and unchanged physical query costs:
1855 original training actions / 288 resets; 3992 reference evaluation actions / 200
resets. Twin training 1043 / 174, twin evaluation 3992 / 200; isolated replay 5 / 1.
These are per-demo figures, not an aggregate of all CI test traffic.

A fresh read-only M6 audit verified 582 folders, 216 cells and 324 scored points and
all frozen source hashes, with zero new benchmark queries. Original scientific records
were not modified. No M6 research campaign was rerun. Unsupported inventory, difficult
rare/delayed paths, unproven query-efficiency superiority, the custom ranker's negative
findings, and the distinction between abstention and correct prediction remain intact.
Finite successful tests do not prove arbitrary-software equivalence.

## Exact private upload and preservation

The isolated checkout is `work/m82-release`, with main tracking the approved private
remote. The final commit contains **204 reviewed files / 7,093,579 bytes**. Every tracked
Git blob was verified against local bytes; scientific data and frozen inputs retain
their bytes. Raw logs, environments, caches, local account metadata and the full research
archive were excluded. The large unchanged evidence archive remains local and available
for separately approved review, not silently uploaded to Git history.

The original project's 51 staged object IDs/modes and index remain unchanged:
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
No unrelated repository was changed. Author configuration was not applied to the original
repository or global settings. No local workbench server was launched during M8.2.

Evidence: `evidence/m82/final-validation.json`, final job logs, extracted reproduction
receipts, transmission inventories, identity verification and screenshots. Historical
M8/M8.1 reports retain their dated findings. This final local results report was written
after the green run; it does not change or claim to be part of the verified remote commit.
The private source candidate points readers to Actions for revision-specific status.

The technical gates defined for this bounded research candidate have passed. Public
publication, visibility changes, release creation and hosting still require separate
explicit owner approval; none occurred.
