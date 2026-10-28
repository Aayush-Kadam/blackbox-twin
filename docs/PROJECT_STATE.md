# Continuation state — 2026-10-28

## Current checkpoint — M8.3 source launch preparation

The owner conditionally authorized public source availability for the exact repository
Aayush-Kadam/blackbox-twin after history, disclosure and final CI checks. The six-job
M8.2 matrix passed on a6c8a1053fab3441586795b733b707a616e4f5b5; see
[executed results](M82_VALIDATION_RESULTS.md). README, current notices and the developer
guide now distinguish closed engineering gates from scientific limitations.

The GitHub connector does not support changing repository visibility. The repository
remains private until the owner completes GitHub Settings after final validation.
No public availability is claimed by this checkpoint. PyPI, hosting, releases, tags,
DOIs, datasets and collaborator changes remain outside authorization.

All sections below are historical checkpoints. Their original verdicts are preserved
and superseded only where the current results explicitly close a gate.

## M8.2 authorization and private validation checkpoint

Owner selected Apache-2.0 and confirmed licensing authority for original contributions,
Copyright 2026 Aayush Kadam. LICENSE/NOTICE and package metadata now reflect approval;
separate upstream notices remain intact. No conflicting original-code ownership claim
or separate-permission exception was found in the reviewed material.

Owner authorized the private Aayush-Kadam/blackbox-twin repository, reviewed selected-file
commits/pushes, hosted Windows/Ubuntu CI and necessary validation fixes. The repository
was created private and empty. Git author identity was explicitly supplied and its noreply
email verified against GitHub settings. Only the isolated release checkout is configured.
No global Git setting or credential value was extracted or modified.

The original 51-file staged index is preserved. Upload scope is the allowlisted source/data
copy plus reviewed licensing/documentation/CI changes, not raw operational logs, local
metadata, environments or the full historical research archive. Exact transmission
inventory is retained in local M8.2 evidence. Hosted results are revision-specific; see
the private Actions page and M82_PRIVATE_VALIDATION.md. No prepared workflow is counted
as passed, and public visibility, releases, hosting and deployment remain unauthorized.

The following M8.1 checkpoint is historical and records the pre-approval gates.

## Current checkpoint — M8.1 completed, NOT READY for public release

M8.1 closed the fresh frontend-installation gate: pnpm 11.25.0, empty node_modules/store,
six downloaded / zero reused packages, unchanged frozen lock, 11 tests passed, production
build and Prettier passed. Supported configuration uses a project-local store, hoisted
layout and copied imports; no OS permissions or lockfile were changed. The clean build
now emits full MIT runtime notices into the wheel, in addition to linked legal comments.

Windows 3.12.10: **182 passed, 7 skipped, 1 warning, 126.51 s**. Windows 3.11.16:
**182 passed, 7 skipped, 1 warning, 122.09 s**. Focused: 41 passed / 7 skipped. Four prior
plus three new physical link/junction cases still cannot create OS links; physical
containment remains NOT VERIFIED and release-blocking. A supplementary dangling-root
test exposed a narrow storage admission issue; using lstat instead of exists fixes it.
The supported same-user trust model and concurrent path-replacement race remain disclosed.
CI now requires physical creation (denial fails); one strict local probe failed the
creation prerequisite as expected and did not establish physical containment.

Fresh non-editable Python wheel + fresh frontend reproduced the bounded supported pipeline
in **47.153 s**, with original costs/scores unchanged: 1 → 5 states, 10 → 5 action witness,
35/35 regressions, 73/100 → 100/100 frozen traces. Independent twin replay, four typed
labels and zero-query unsupported inventory passed. Real browser/backend smoke passed;
owned server PID exited and tab closed. No new campaign or scientific scoring change.
Read-only M6 audit: **582 folders / 216 cells / 324 points** preserved.

Expanded exact-version advisory review: **47 completed OSV queries**, no listed advisories,
including pnpm/platform esbuild and setuptools vendored packages. Not vulnerability-free
certification. Upstream pydot MIT/Python-2.0 and setuptools notices were recovered from
hash-verified sdists; AALpy's sdist omitted its license, so a commit-pinned repository
fallback is recorded explicitly. Full runtime React licenses are bundled and served.
Owner provisional preference: Apache-2.0. **LICENSE NOT SELECTED — OWNER DECISION REQUIRED**;
no final license or holder assertion was added. See M81_APACHE_REVIEW.md.

Distribution scan: about 0.95 GB of non-cache evidence; no credential-pattern matches,
but personal paths in 47 files and email-like strings in 31 files, mostly historical
reports/upstream attribution. Values withheld, originals preserved. Current 51-file index
is an older incomplete state with a personal-path document: do not publish it as-is.
Scoped ignore additions exclude new/raw audit material without unstaging tracked files.
A local allowlisted source review copy and unchanged compressed campaign archive are
prepared under `work/m81-public-review`, with exact path/size/SHA256 inventory and a
derived redacted document copy. Nothing was staged or removed to prepare that copy.

CI is prepared for hosted Windows/Ubuntu × Python 3.11/3.12 plus frontend on both OSes,
least-privilege read permissions, required physical tests, packaging and bounded smoke.
**CI NOT EXECUTED; Linux NOT VERIFIED.** No remote or HEAD commit exists. Explicit owner
authorization for a named private remote and selected-file commit/push/workflow run is
needed. Ownership/license confirmation is separate; public release/visibility changes
require separate approval after actual gates pass. Not one licensing decision away.

Authoritative report: `M8_1_RELEASE_READINESS.md`; entry matrix: `M8_1_GATES.md`.
New evidence: `evidence/m81/`, original/new command logs in `work/m81-*`, public dependency
notices in `third_party/`. Added CI package smoke, source/distribution review and license
collection helpers; new physical/supplementary filesystem tests. M8 evidence is retained.
No staging, commit, reset, push, remote creation, PR, hosted workflow, publication,
deployment or visibility change. Index SHA256 remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.

## Historical M8 checkpoint — NOT READY for public release

Recovered and continued the interrupted M8 session without replacing prior logs or
historical experiments. Final verdict: **NOT READY** for public release; suitable for
continued local technical review. **LICENSE NOT SELECTED — OWNER DECISION REQUIRED**.
Other gates: upstream attribution closure, four unverified physical link/junction cases,
and a fresh frontend installation blocked by Windows symlink restrictions. Linux remains
**NOT VERIFIED**; CI was prepared locally and has not executed remotely.

Security implemented: resolved evidence/export containment and fixture path guard,
subprocess environment allowlist, one-worker/three-run admission, 64 MiB storage admission,
bounded traversal, strict Host/origin/method checks, bounded request body/deadline/JSON
depth, sanitized errors and response headers. No OS sandbox or hostile-code execution
guarantee. Patched FastAPI 0.162.0 / Starlette 1.10.0 and setuptools 84.1.0. Full dependency
closure audit: 33 exact-version OSV queries completed, no listed advisories for final
versions; seven original GHSA records and their remediation are preserved. This is not
a claim that the dependency tree is vulnerability-free.

Windows 3.12.10: **180 passed, 4 skipped, 1 warning, 156.18 s**. Windows 3.11.16:
**180 passed, 4 skipped, 3 warnings, 160.28 s**. These are the same suite on two interpreters.
Focused changed-component run: 39 passed / 4 skipped. Physical OS link/junction creation
was not permitted; logical path checks do not replace it. Frontend 11 tests, production
build, Prettier, Python Ruff lint and formatting passed with existing installed frontend
dependencies. Fresh frontend installation remains BLOCKED, not passed.

Fresh non-editable wheel + declared 29-file / 5,831,724-byte data kit reproduced the
supported pipeline in 88.496 s: 1 → 5 states, 10 → 5 action witness, 35/35 regressions,
73/100 → 100/100 frozen traces. Per-run original training 1855 actions / 288 resets,
paired evaluation 3992 / 200; twin training 1043 / 174, evaluation 3992 / 200, isolated
replay 5 / 1. Typed statuses/refusals and unsupported inventory were reproduced.
Two additional sequential installed demos took 53.535 / 54.691 s and matched these
costs/scores. Native profiling sampled 97.293 MiB peak summed working set, 61.594 MiB
private commit, 89.969 CPU seconds and six processes; browser memory is excluded.
Original immediate cleanup check returned FAIL; a retained-exit-record bug was corrected
and separate follow-up verified no recorded owned PIDs or temporary directories remained.
Original failed profile/logs are preserved. No expensive demonstration rerun was used
to obtain a nicer status.

Read-only integrity audits: M3, M5, M5.1, historical M7 and all fresh M8 runs passed.
M6: **582 folders / 216 cells / 324 points** preserved, frozen source hashes intact.
Current oracle environment hardening differs from historical code, explicitly recorded.
M4 negative findings retained and regression-tested; its historical forensic writer was
not rerun. No M6 campaign rerun. Inventory unsupported; efficiency superiority unproven.

Real browser smoke used the independently installed Python 3.11 server: replay, typed
ambiguity/unknown cascade and inventory failures visible, no captured console errors.
Temporary browser tab closed; servers and recorded owned child PIDs stopped. Browser
server exit was verified; its PTY Ctrl+C did not capture a graceful shutdown log.
Profiling server did log graceful application shutdown. No public listener was started.

Current authoritative reports: `M8_VERIFICATION.md`, `M8_THREAT_MODEL.md`,
`M8_DEPENDENCIES.md`, `M8_RECOVERY.md`, `DEVELOPER_GUIDE.md`, `LICENSING.md`,
`RELEASE_CHECKLIST.md`, root `THIRD_PARTY_NOTICES.md`. Evidence under `evidence/m8-*`;
final verification logs/clean reproduction copied into `evidence/m8-verification/`.
Original workspace logs and wheel/data kit remain under `work/m8-*`.

Changed runtime modules: m7_data, m7_demo, oracle, workbench; new local_boundary/run_limits.
Also changed pyproject build/web pins, local CI, README, audit_m7 and docs. New security
tests and M8 dependency/report, kit/reproduction, edge-check and profiling scripts are
included. No learning algorithm or scientific benchmark results were changed.
Git index SHA256 remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
Existing staged work is preserved. No staging, commit, push, publish, release, deployment
or visibility changes. Owner decisions and blocked verification remain explicit; no
automatic public release continuation is authorized.

## Historical M7 state — 2026-10-27

### M7 complete with limitations

The M7 continuation explicitly authorized ordinary local implementation. The original
scope was recovered from the roadmap and master build prompt: **React + FastAPI interactive
scientific workbench**, compatible with the continuation priorities. No scope conflict.

Implemented: local backend/production React assets, allowlisted experiment explorer,
learned-state graph/transition inspection, persisted differential comparison and divergence,
original/minimized counterexamples, before/after models, bounded fresh demonstration,
phase-separated query/reset costs, physical event pagination, validated model/twin exports,
typed support/evidence preview with unknown-state/reset policy, and all M6 benchmark points.
Core M3/M5/M6 source modules and experimental strategy availability/defaults are unchanged.

**M7 PASS WITH LIMITATIONS. M8 READY WITH LIMITATIONS.** No M8 implementation started.
154 Python tests passed (245.26 s, one dependency deprecation warning); after the final
M7 metadata/request/provenance edits, all 13 affected tests passed again (2.07 s).
11 frontend rendering tests passed; production build, Prettier, full Ruff lint and formatting
of 70 Python files passed. Real desktop browser checks passed for replay, revision changes,
fresh execution, support/refusal/reset, invalid input and inventory failures. Screenshots
and transcripts: `evidence/m7-verification/browser/`. Mobile/cross-platform/UI usability
studies are not claimed. The browser download prompt was not exercised; HTTP export bytes
and headers were verified in Python tests.

Fresh CLI development run: `runs/m7-primary` (48.306 s). Final live browser run:
`runs/m7-live/live-bb4f6a1d66fb440da8b54a00ceb82de0` (50.338 s). New non-editable environment
`work/m7-clean-venv` reproduced the full demo in `runs/m7-clean-reproduction` (56.623 s),
matching behavioral tables, action/reset costs, frozen scores and installed asset hashes.
Each run: original training 1,855 actions / 288 resets, separate original paired evaluation
3,992 / 200; twin training 1,043 / 174, twin evaluation 3,992 / 200, isolated replay 5 / 1.
Three-run original total 17,541 actions / 1,464 resets, excluding test-suite traffic.
One-state initial model -> five-state refined model; real 10-action mismatch -> five-action
deletion-local witness; 35/35 regressions passed; exact frozen traces 73/100 -> 100/100,
outputs 1967/1996 -> 1996/1996. No universal equivalence or new benchmark claim.

`live-audit.json` / `clean-audit.json` reconcile all physical counts and score denominators.
The two final runs froze source/fixture/input hashes before learning. The earlier CLI run
is retained as development evidence. `m6-preservation.json` verified 582 immutable artifact
folders and reconciled all 216 M6 cells / 324 points, with all preexisting engine-source
hashes matching. Zero original queries were used for that preservation check or typed
previews. M6's scientific verdict, including unsupported inventory and failed efficiency
superiority, remains intact. This milestone did not revisit the custom ranker.

New/changed files: `src/blackbox_twin/{m7_demo,m7_data,workbench}.py`, bundled
`workbench_assets/`, `frontend/` sources/build/tests/package/lock files, optional extras
and package-data configuration in `pyproject.toml`, `requirements-workbench-lock.txt`,
`tests/test_workbench.py`, `scripts/{audit_m7,reproduce_m7}.py`, M7 workbench/verification
docs, README, architecture, roadmap and this state document. No historical evidence was
edited. Git index hash remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
No staging, commit, push, publication, visibility change or remote resource occurred.

See `M7_WORKBENCH.md` for concise start/rebuild/reproduction commands and limitations;
`M7_VERIFICATION.md` records successful/failed commands and evidence paths. Original new
test expected the wrong response key and failed; corrected to the actual fixture contract.
An initial reader counted twins as original traffic; it failed closed, was corrected and
regression-tested. Installation failures (cache permissions, registry connectivity and
pnpm registration symlinks) were resolved with workspace caches, granted network access
and a contained store, without enabling ignored install scripts. No file-edit review
denial or bypass occurred.

The verification server was stopped after jobs completed; process/port checks are saved
with final evidence. Live failed jobs are visible during that server session; partial
folders remain on disk, while the persistent experiment selector lists completed demos.
Do not rerun completed demos merely for nicer output. Starting a fresh demo is an explicit
user action and always creates a new folder. For review, use saved evidence first.

Next milestone is M8 hardening, requiring user continuation: cross-platform verification,
profiling, dependency/security/license review, CI coverage for optional workbench/frontend
and owner-approved release preparation. No public deployment or release is authorized.
The old M6 runner's full source-map guard intentionally rejects the expanded M7 package;
use the frozen M6 source snapshot for exact M6 reproduction, never alter its manifest.

## Historical checkpoint — M6 closure

The owner authorized normal reviewed creation of `src/blackbox_twin/m6_train.py`; review
accepted it. The earlier usage-based denial was not bypassed. New M6 adapters, target
generators and sequential resumable runner are implemented. Eleven M6 tests are included
in the final full suite: **141 passed in 171.15 seconds**. Full lint passed and all 64
Python files passed formatting checks. Existing Windows tests/timeouts were not weakened.
Nine pilot cells completed (5,241 training actions / 1,825 resets). A pilot-only regression
budget-status defect was fixed and the affected adaptive adapter rechecked at 1,500 actions;
it now stops as action_budget with 45/45 completed regressions, instead of labelling
budget-truncated verification complete. Original pilot and source snapshots are preserved.

`benchmarks/manifests/m6-v1.json` is frozen. Sequential confirmation completed at
`evidence/m6-confirmatory-v1/`: **216 cells / 324 scored points**, including 24 explicit
guarded-inventory compatibility rejections with zero training calls. No package source
changed after freezing. Actual cost: 214,815 original training actions / 51,022 resets;
references 45,550 actions / 3,811 resets; separate twin cost 695,272 actions / 52,914 resets.
Campaign elapsed 662.22 seconds, no partial-attempt costs, zero unexpected failed cells.
Three finite learner seeds / two typed learner seeds; independently drawn target, learner,
training and evaluation streams. Budgets A250/1000, B1500/3000, C500/1500. Twenty-one target
instances include the historical rare fixture and known delayed-depth regression structure.
There are 3,811 frozen sequences / 48,972 scored trace executions. Do not count repeated
seeds/checkpoints as independent targets. Exhaustive diagnostics overlap training; random
and challenge full-word overlap is zero. All intersections are disclosed in the audit.

Both physical/metric and support-evidence audits passed. All 24 hardened models recompiled;
1,952 observations reconciled to physical evidence. Non-editable offline installation and
three representative retrainings passed, matching costs/policies; 6,406 isolated twin
requests passed, including the inventory refusal policy. This does not imply correct
inventory reconstruction. Reproduction cost 3,717 original actions / 1,046 resets is separate.

Engineering **PASS WITH LIMITATIONS**. A finite reconstruction and B typed generalization
are PARTIALLY SUPPORTED; C abstention is SUPPORTED within the bounded wallet class; D query
efficiency superiority is NOT SUPPORTED. M4's negative custom-ranker verdict is unchanged.
M7 **READY WITH LIMITATIONS**, but no M7 work started. All rare highest-budget models fail
finite equivalence; hardened wallet fidelity trails adaptive on five of six target means;
inventory guarded inference is incompatible and all concrete runs exhaust budget before
a complete hypothesis. 138/216 cells did not reach the fidelity/coverage criterion.

Files implemented/retained: `src/blackbox_twin/m6_train.py`, `m6_targets.py`, `m6_run.py`,
the optional seed/oracle-factory extension in `typed_learning.py`, `tests/test_m6.py`,
`scripts/run_m6.py`, `audit_m6.py`, `audit_m6_support.py`, `analyze_m6.py`, `reproduce_m6.py`,
the frozen manifest, M6 protocol/support/recovery/results/failure/verification documents
and README. See `M6_VERIFICATION.md` for exact successful and failed command history and
`evidence/m6-verification/` for final logs. Earlier baseline/pilot failures are preserved.
No current file-edit blocker: owner-approved normal resubmission was accepted. No bypass.

The Git index SHA256 remains
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
No staging/commit/push/publication occurred. Next permitted work is read-only review or
explicitly requested continuation; do not automatically start M7 or rerun completed
expensive cells. If interruption recovery is needed, inspect saved evidence first and
use matching source/protocol `--resume`; live learner-table continuation is not claimed.

The recovery checkpoint below is historical; its missing-file/blocked statements describe
the state before the owner's explicit authorization and successful reviewed creation.

## M6 interrupted-session recovery checkpoint

**M6.0 preparation only; blocked training implementation; no frozen protocol or pilot.**
Read `M6_RECOVERY.md` before continuing. The retained three-track protocol is a draft;
`benchmarks/manifests/m6-v1.json` is absent. Retained M6 edits are the protocol draft,
`m6_targets.py` and optional seed/factory injection in `typed_learning.initialize`.

The proposed `src/blackbox_twin/m6_train.py` creation was not executed: automatic review
could not complete because of a usage limit, with no unsafe-content determination.
The file is absent and there are no partial contents. The owner explicitly prohibited
bypassing that declined action through another editing route. Resubmission through
normal review requires owner direction, requested during recovery. Do not infer that
a new session or working tools automatically authorizes resubmission.

No M6 pilot, training cell, reference acquisition or confirmatory result exists. Planned
learner seeds remain three for finite / two for typed, actual executed M6 learner seeds
zero. The two-counter inventory remains outside the guarded model class; do not invent
transfer support. No large suite or M7 work has started.

Verification: prior baseline runs each had 129 passes/1 failure (Windows cleanup teardown,
then subprocess termination timeout). Recovery reran the three relevant unchanged tests:
3 passed in 4.75 s. Six static development source-generation checks passed with zero
oracle calls. Focused lint reports 14 line-length findings in unfinished `m6_targets.py`.
No current full-suite or lint pass is claimed; preserve the original failures and rerun
the full suite after legitimate implementation/technical fixes. Tests were not weakened.

Recovery evidence: `evidence/m6-recovery/`. Next: resolve authorization for the denied
creation, finish infrastructure, pass a small pilot, then freeze and execute the bounded
campaign. Everything below is historical M5.1 and earlier continuation context.

## M5.1 continuation checkpoint

**M5.1 engineering PASS (bounded wallet class); M6 READY WITH LIMITATIONS.** M6 has not
started. M4's negative result and M5's PASS WITH LIMITATIONS/data remain historical facts.
Current wallet support policy is version 3; older formats/commands remain reproducible.

Read `M5_1_DIAGNOSIS.md`, `M5_SUPPORT_POLICY.md` and `M5_1_VERIFICATION.md`.
New modules `support.py`, `support_runtime.py`, `m51.py` enumerate the full bounded guard
function space, preserve all compatible updates, compile per-context support regions,
and emit OBSERVED / INFERRED_SUPPORTED / AMBIGUOUS / UNSUPPORTED metadata. Direct same-state
observations are a verified fallback. Refusals invalidate session state until trusted
reset. `--explain` on generated twins provides provenance without changing normal payloads.
Native StatePrefix remains the underlying state learner; no M4 ranker revival.

Autopsy: all 11 failing B unseen traces first hit overlapping selected guards on deposit(2)
at active balance zero. Two exhaustive B cases separately contain wrong concrete
withdraw(2) error classifications. The new policy labels these cases as abstentions,
not successes: 19/30 unseen traces still match, 11 abstain; 264/272 contextual traces
match, 8 abstain. These historical cases are development regressions, not fresh holdout.

Fresh protocol `benchmarks/manifests/m5-1-fresh.json` and raw source were frozen before
execution. Target/probe/evaluation seeds are separate; new reserved values include 3,
while 2 is permitted. Two new randomly selected configurations both have cap 1 (limits
2 and 1); no replacement/tuning after results. Six training cells compare old fixed grid,
old adaptive and hardened; two policy-only conversions share old adaptive observations.
CLI: `bbt typed-harden --protocol <frozen-json> --out <fresh-folder>`; installed use needs
`--project <source-root>` for the owned fixture. Existing `typed` is the historical M5 flow.

Hardened fresh results: 22/30 and 30/30 unseen traces, 161/215 and 215/215 exact outputs;
coverage 74.884% / 100%, conditional accuracy 100%, false-supported 0%, abstention
25.116% / 0%. Exhaustive agreement 132/136 and 136/136. These match old adaptive here;
there is no fresh fidelity superiority claim. Guard precision/recall 1/1 in these small
populations. Actual ambiguity probes 9 and 6; hardened observed regressions 61/61 and 58/58.
Post-hoc pre-probe component checks show lower coverage, explicitly separately labelled.

Primary original training: 7,704 actions / 2,688 resets; shared original evaluation:
1,850 / 448 separately; total including references 9,554 / 3,136. Primary twin executions
10,854 / 2,598 separately. Full support recompilation, event provenance, budgets, no reserved
training values, zero held-out full-word overlaps and metric recounts pass audit.
Primary data: `evidence/m5-1-fresh/`; audit `evidence/m5-1-audit.json`.

Latest full suite: **130 passed, 0 failed in 144.85 s**; 111 prior tests unchanged plus
19 new cases. Focused standalone/budget/context/file-isolation checks also pass. Lint /
format pass, no type checker configured. A non-editable installed fresh-0 hardening run
reproduces 1,233 actions / 456 resets, identical model ID/cells/regressions; isolated plain
and explained twins reproduce all 224 policy cases including abstentions, not 100% target
fidelity. Historical M2/M3/M5 audits still pass; M4 frozen evidence remains preserved.
No commits, pushes, releases or new dependencies. Index tree unchanged:
`9d804578899a21849533231252b1a2fbb7e23059`.

Next: a separately requested M6 can benchmark broader **declared** wallet conditions,
larger caps and model-class violations while reporting coverage and conditional/end-to-end
accuracy together. Remaining assumptions: observable-state sufficiency, discovered output
vocabulary, three-term linear guards, bounded integers and restricted updates. No hidden
registers, symbolic references or arbitrary schemas. Do not begin M6 automatically.
Everything below is preserved historical continuation context.

## M5 continuation checkpoint

**M5 PASS WITH LIMITATIONS.** M5.0–M5.4 bounded typed-wallet pipeline is implemented;
M5.5 evaluation/reproduction completed with material generalization limits. Native
StatePrefix remains recommended; the M4 custom ranker remains experimental and its
performance verdict remains NOT SUPPORTED. No M6 work or publication was started.

Read `M5_WALLET_CONTRACT.md`, `M5_MODEL_SPEC.md`, `M5_EXPERIMENTS.md` and
`M5_VERIFICATION.md`. Versioned contract: `examples/typed_wallet/contract.json`, frozen
with owned fixture/configuration hashes before inference. Integer amounts -8..8, balance
0..4, observable frozen state, deposit/withdraw/get_balance/freeze/unfreeze. Boolean,
enum, optional/nullability schemas are supported by infrastructure, not inferred for
additional wallet fields. Symbolic references/general register learning are not implemented.

New modules: `typed.py`, `typed_runtime.py`, `guards.py`, `typed_learning.py`, `m5.py`.
Existing synthesis dispatches model versions; M3 differential comparison/minimization,
Session, Recorder and replay cache are reused. New `bbt typed --out <fresh-folder>` runs
the two-variant fixed-grid/adaptive evaluation; `--development` selects the separate
development configuration. Installed use requires `--project <source-project-root>`.

Primary: `evidence/m5-primary/`. A adaptive: 340/340 exhaustive contextual cases and
30/30 unseen sequences. B adaptive: 264/272 exhaustive cases but only 19/30 unseen
sequences, below fixed grid's 29/30. A learned real amount/balance guards and add/subtract
updates that handle never-trained amount 2. B's underdetermined cuts/relations remain
unresolved; do not retune on these evaluation outputs or claim universal generalization.
Actual minimized CEs are deposit(4) in A and deposit(3) in B; both final replays agree.
163/163 and 127/127 contextual regressions pass. Final models are revision-004.

Primary original training: 6,412 actions / 2,157 resets; shared original evaluation:
4,055 / 858 separately. Twin calls: 9,233 / 2,030 separately. Every phase and reserved
value/held-out sequence separation is audited. `evidence/m5-audit.json` is PASS.
One non-editable adaptive A reproduction matches 2,112 / 666 and model rules/states;
the isolated standard-library twin matches all 470 cases with package loading disabled.

Latest complete suite: **111 passed, zero failed in 140.70 s**; 23 M5 cases added to the
previous 88 unchanged tests. Lint and formatting pass (50 files). M2, M3 and frozen-source
M4 evidence audits still pass. No type checker configured. Source snapshots and one
AST-identical formatting amendment preserve exact historical training fingerprints.
Git index tree remains `9d804578899a21849533231252b1a2fbb7e23059`; no commits/pushes.

Next recommended action: a separately specified ambiguity/support-policy robustness
follow-up using new untouched configurations. **Hold the broader M6 benchmark campaign.**
Do not claim M5's adaptive method uniformly improves fidelity or query efficiency.
The remainder of this document is historical continuation context; its statements about
M5 being unimplemented apply to their earlier milestone dates.

## M4.1 continuation checkpoint

**M4.1 COMPLETE WITH LIMITATIONS; Outcome B (algorithmic weakness).** Historical M4
performance remains NOT SUPPORTED. Native AALpy StatePrefix is now the recommended
`bbt learn` default (25 walks/state, 12-input tails, finite sampled stopping).
All eight strategies remain selectable; custom ranking is experimental/underperforming.
Historical low-level learner/M3 defaults remain reproducible; `learning_options()` selects
the recommended application policy. No M5 functionality was implemented.

Latest verification: **88 passed, zero failed, 162.61 s**, Ruff lint/format pass.
Six focused tests add controlled feature/order/tie/budget checks, bounded diagnostics,
default selection and strategy preservation. Default CLI export smoke completed; another
budget-exhausted smoke is preserved honestly. Metadata now identifies the actual delegated
oracle instead of always claiming Random W. No score/generation defect was found.

Read `M4_1_DIAGNOSIS.md` for evidence, costs and unresolved causal factors. The diagnostic
sprint spent 6,482 actions / 1,346 resets; including an aborted instrumentation attempt
and two separate CLI checks, non-test totals are 8,270 / 1,553. No replacement planner,
retuning or confirmatory rerun occurred. Coverage ablation changes choices in all 15 pairs;
suffix ablation changes 13/15, despite identical historical checkpoint curves.

Frozen M4 hashed source is preserved at `evidence/m4-confirmatory/source-snapshot/`.
Its independent audit still passes (120 cells / 480 checkpoints). New `learning.py`
metadata intentionally changes the current source digest: use the frozen snapshot for
historical audit; never change historical hashes or resume old cells with new source.
Git index tree remains `9d804578899a21849533231252b1a2fbb7e23059`; no commits/pushes.

Next: review `M5_READINESS.md`, freeze the bounded typed-wallet protocol, then begin M5
only under a separate implementation instruction. The remaining text is historical M4
and earlier continuation context, retained without revising those milestone results.

## Historical M4 checkpoint

Current checkpoint: **M4 engineering PASS WITH LIMITATIONS; performance NOT SUPPORTED**.
M3 remains PASS; M0–M2 remain PASS WITH LIMITATIONS. The project is not release-ready.
Recommendation: reconsider the current ranker and wait for the owner's next direction;
do not automatically implement M5.

Last verified commit: **none**. Git is initialized and files are staged. A local commit
was attempted but author identity is missing; no identity was invented. The pre-report
staged source/evidence tree was `eeedaa3c5a51fbecbfd9a3c51e4486279a53993b`.
That was a historical tree ID, not a commit. The current staged tree remains
`9d804578899a21849533231252b1a2fbb7e23059`, unchanged through M4.
Existing staged entries were preserved; M3/M4 work is saved as working-tree changes/new files.
Latest verification: **82 passed, 0 failed in 221.89 seconds**; lint/format passed
(36 files formatted), primary SQL/hash/score audit passed. M4 adds 20 tests to the prior
62, including common-cache physical accounting, leakage guards, interrupted evidence
and actual M3 planner/refinement integration. No static type checker is configured.
See `M4_VERIFICATION.md`, `M4_RESULTS.md` and the historical M3 report. The original index
tree is unchanged; M4 additions and modifications remain saved in the working tree.

## Working environment

Project: `outputs/blackbox-twin` relative to the enclosing workspace. Development Python:
`work/.venv/Scripts/python.exe`; installed CLI: `work/.venv/Scripts/bbt.exe`.
Non-editable reproduction environment: `work/clean-venv`, reinstalled with M4 code.
The portable setup and project-relative
commands are in README. `requirements-lock.txt` records installed versions.

Use new output directories for each CLI run. The preserved successful M2 sample is
`evidence/demo-training-v2`, held-out output is `evidence/demo-heldout`. The initial failed
cleanup run remains in `evidence/demo-training`, with its failure explained. Do not relabel
it successful or overwrite it. Temporary test/process/package caches live in workspace `work/`.

## Completed M4 evidence

Primary: `evidence/m4-confirmatory/`, manifest `benchmarks/manifests/m4-confirmatory.json`.
Three families, five paired seeds each (target 201–205, selection 100201–100205,
evaluation 200201–200205), eight methods, four action ceilings 250/500/1000/2000.
There are 15 paired configurations and 10 distinct programs (5 random, 4 delayed,
1 repeated workflow). Each pair shares 80 frozen reference words, isolated from training.
120 cells and 480 checkpoints were audited; no failed/recovered primary cells.

The full cost-aware method had zero AULC wins against either native baseline. It reached
95% in 13/15 cases versus 15/15 for both native policies. Median AULC 0.7109375 versus
0.7703125; resets and runtime were worse. Coverage and separator ablations gave identical
measured curves. Cost removal was mixed and reached 14/15. This is a negative performance
result, not a novelty or universal impossibility claim.

Primary costs: 239,861 training actions / 42,066 resets; shared references 33,780 / 1,200
separately. Total including evaluation: 273,641 / 43,266. Unreached thresholds remain null.
62 cells stopped 1–5 actions short at the final ceiling; comparisons explicitly report
ceilings and actual spending. Six cells reproduced from a non-editable installation with
matching physical counts, counterexamples and all checkpoint scores. The full matrix was
not independently repeated.

The original 101–105 pilot also completed with a negative result. Its data, pre-amendment
audit and source snapshot remain in `evidence/m4-pilot/`. Review noticed coupled
generation/selection seed labels; the confirmatory block corrected only seed separation,
without tuning weights, baseline strength, budgets or metrics. Do not resume the old
output under amended source; digest rejection is expected.

New CLI: `bbt benchmark generate/run/summary/audit`; M3 workflows accept `--strategy cost-aware`.
Completed-cell resume was executed without rerunning cells. Interrupted training attempts
restart fresh and preserve earlier evidence; target/reference-generation interruption is
not a verified recovery path. No live AALpy table resumes. Fixed pilot protocols and all
remaining limits are in `M4_EXPERIMENT_PROTOCOL.md` and `M4_VERIFICATION.md`.

## Completed M3 evidence (historical)

Primary run: `evidence/m3-demo/`. Non-editable reproduction:
`evidence/m3-clean-reproduction/`. Both preserve equal behavioral tables, physical costs
and held-out scores, verified by `scripts/audit_m3_evidence.py`.

The genuinely learned model changed from 1 state (revision 000, ID beginning `693910cf`)
to 5 states (revision 001, ID beginning `8b770ad7`). The discovered sequence was
`idle, commit, advance, advance, advance, idle, advance, commit, commit, advance`.
The replayed deletion-local minimum is `advance, advance, advance, advance, commit`.
First original mismatch: action 8, `/result`, target `accepted`, old twin `denied`.
Both failures were resolved automatically. Regression replay passed 35/35 traces,
preserving all 30 previously passing cases with zero new regressions.

The same 100 pre-frozen words yielded 73/100 -> 100/100 exact traces and
1,967/1,996 -> 1,996/1,996 exact outputs. No full-word training overlap was found;
prefix reuse is expected. These are sampled results, not an equivalence proof.
Original-oracle costs: 1,855 actions/288 resets for the loop; 3,992/200 for paired
evaluation; **5,847/488 including evaluation**. Twins have separate counters.

The interrupted 60-test run finished successfully. Repeating its corrected fault group
found an additional Windows sharing-lock cleanup race. The adapter now uses bounded
sharing-lock retries and retains the primary OracleFailure even if cleanup fails.
Two deterministic regressions were added; all 62 tests then passed. Dedicated short
timeout tests remain. Full detail and exact commands: `M3_VERIFICATION.md`.

## Next engineering decision

Retain native RandomW/StatePrefix references and reconsider the cheap-query/coverage score.
Any redesigned planner needs a new development/evaluation split; the 101–105 and 201–205
sets are now observed and cannot be recycled as untouched evidence. Preserve all M3/M4
regressions. No M5/frontend/symbolic expansion has begun.

## Remaining blockers and decisions

The fixed-protocol pilot is complete with explicit limitations and a negative performance
result. Git author identity is needed only to create a local
commit; project license selection remains an owner decision before public release. M5–M8,
OS-enforced isolation, typed amount/reference support and multi-family baseline evaluation
are pending. No remote repository, external deployment or release has been created.
