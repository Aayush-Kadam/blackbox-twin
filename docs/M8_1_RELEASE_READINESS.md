# M8.1 release readiness — NOT READY

2026-10-28. Fresh frontend installation and bundled attribution deficiencies were
addressed. The supported Windows pipeline works from a fresh package/frontend build.
Public release is still **NOT READY**: physical filesystem boundaries remain unverified,
hosted CI/Linux has not executed, and the owner has not selected a project license or
confirmed ownership. This is not a single-license-decision-away PASS.

## Final gates

| Gate | Result and evidence | Remaining action / authorization |
|---|---|---|
| Windows Python 3.12.10 | 182 passed, 7 skipped, 1 warning; 126.51 s | No functional failure; physical skips remain separate |
| Windows Python 3.11.16 | 182 passed, 7 skipped, 1 warning; 122.09 s | Same 189 tests, not independent extra cases |
| Focused security/workbench | 41 passed, 7 skipped, 1 warning; 8.40 s | Seven real link cases could not create OS links |
| Fresh frontend | PASS: empty node_modules and store, frozen install, 11 tests / 0 failures / 0 skips, production build and Prettier | Install gate closed; no independent ESLint configuration exists |
| Package and end-to-end | PASS: new non-editable 3.12 wheel, declared data kit, full supported demo and actual browser/backend communication | No arbitrary-target or equivalence claim |
| Windows filesystem security | NOT VERIFIED physically; supplementary checks passed | Execute strict physical tests on a permitted host; no system-policy changes authorized |
| Linux | NOT VERIFIED | Actual hosted Linux execution required |
| CI | Prepared and locally parsed/formatted, NOT EXECUTED remotely | Owner must authorize a named remote and selected-file commit/push/workflow execution |
| Dependencies | 47 exact-version OSV queries completed, no listed advisories | Dated source coverage, not vulnerability-free certification |
| Attribution | Bundled full MIT notices fixed; upstream texts/provenance collected | Owner reviews scope/rights and AALpy repository fallback provenance |
| Project license | LICENSE NOT SELECTED — OWNER DECISION REQUIRED | Confirm Apache-2.0 and copyright holder(s), after review |
| Scientific integrity | Read-only M6 and fresh-run audits PASS; 582 folders / 216 cells / 324 checkpoints | No research campaign rerun or score changes |
| Distribution hygiene | Inventory and conservative scan completed; local allowlisted review copy prepared | Do not publish current Git index or use indiscriminate add-all |

Logs and machine evidence are retained in `evidence/m81/` and workspace `work/m81-*`.
The entry gate matrix is `M8_1_GATES.md`; M8 reports and failures remain unchanged.
The sole warning in the final interpreter suites is the existing HTTPX TestClient
deprecation. No warning suppression, weakened assertion or relaxed timeout was introduced.

## Fresh frontend: diagnosed and closed

M8's pnpm 11.25.0 failed while registering an external store project symlink, before
dependency installation. This was a filesystem operation, not a broken lockfile, registry
resolution problem, dependency incompatibility or post-install failure.

`frontend/package.json` now declares pnpm 11.25.0, matching the actual tested executable.
`frontend/pnpm-workspace.yaml` selects `nodeLinker: hoisted`, `packageImportMethod: copy`
and `storeDir: .pnpm-store`. pnpm documents its flat package layout; the installed pnpm
source registers projects only when the store is external to the project. This supported
configuration removes an unnecessary link operation; no access policy, privileges, tool
source or integrity checks were changed. The fresh store and node_modules were absent
before installation; the install downloaded six packages and reused zero packages.
Lifecycle scripts remained disabled, and the declared optional esbuild platform binary
worked. Existing populated node_modules were not used to establish installation success.

Lock SHA256 before/after:
`62A9D3DAB994F7818117D33BA9910B5B5072F2A5C7776E63838D47409B185721`.
No dependency resolution or lockfile was changed. Clean tests: 11/11, build and formatting
passed. Python Ruff lint/format also passed. No separate frontend semantic linter is
configured or falsely counted as executed. The new build emits complete upstream MIT
texts, and the clean wheel served those exact bytes through its actual backend.

## Filesystem security: still blocked

The four M8 physical cases plus three new physical cases all skipped because Windows
denied owned symlink and junction creation. New cases cover a broken output-root link,
a two-link chain escaping the root and replacement before revalidation. No privileged
settings were enabled, no alternative low-level link API was used and no experiment ran
outside the approved workspace. No physical containment assertion was reached or failed;
the creation prerequisite is unavailable. These seven cases remain NOT VERIFIED.

A supplementary metadata test found and fixed a narrow admission issue: `exists()` follows
links, so a dangling output-root link could appear missing. `storage_size` now uses lstat
and rejects its reparse/link metadata instead of admitting it as zero storage. Two
supplementary tests pass; they do not substitute for actual OS behavior.
Replacement before validation is covered by the physical test, not atomic concurrent
replacement during an open. The same-user race and lack of OS isolation remain disclosed.

Hosted CI sets BBT_REQUIRE_PHYSICAL_LINKS=1: denied link creation fails instead of silently
skipping. A local strict probe produced the expected one prerequisite failure, zero skips,
and four deselected tests; it demonstrates the gate, not a passing physical test. Normal
suites retain honest skips locally. Broader Windows filesystem signoff remains blocked.

## CI preparation

The local workflow prepares Windows/Ubuntu × Python 3.11/3.12, plus fresh frontend
install/test/build/format on both operating systems. Python jobs include full tests,
lint/format, wheel build and a bounded independent package/data-kit smoke script. They
do not run the M6 campaign. Global permissions are contents:read, checkout credential
persistence is disabled, jobs have time limits, and there are no deployment steps,
secrets or self-hosted runners. YAML parsing/formatting and Python script lint passed.

No remote jobs were triggered. The local repository has no HEAD commit and no remotes;
its 51 original staged files represent an older incomplete state. An authorized selected
source commit/push to a named remote is required before hosted CI can supply platform
evidence. Prepared jobs are not green jobs. No WSL/Docker restrictions were bypassed.

## Attribution and licensing

The production bundle contains React 19.2.0, react-dom 19.2.0 and scheduler 0.27.0. It now
includes full MIT license/copyright texts in THIRD_PARTY_LICENSES.txt, alongside esbuild's
linked legal comments. The original project modules, fixtures, generated interpreter
templates and documentation require owner confirmation; generated behavioral hypotheses
retain provenance and are not relabelled universally equivalent or third-party code.
No third-party font/image/icon files are bundled: styles use system fonts and project
markup. Screenshots, environments and downloaded tool archives are excluded.

Exact-version PyPI sdists were downloaded and SHA256-verified. pydot's texts live under
LICENSES/ (MIT and Python-2.0); setuptools' root license was collected. AALpy's 2.0.0
sdist omits its license text; a commit-pinned upstream LICENCE.txt fallback is recorded
without pretending it came from that release archive. The collector's first attempt missed
subdirectory texts and reused basenames; corrected path-preserving collection is retained
separately. Public notices/provenance are under `third_party/`; full local audit material
is in `evidence/m81/attribution/`. Tool/vendor license texts do not relicense project code.

No conflict was identified for the actually bundled MIT material with proposed Apache
terms when upstream notices are retained. This is a limited compatibility review, not
ownership clearance. `M81_APACHE_REVIEW.md` records recommendation, proposed copyright
wording and exclusions. No final project LICENSE, legal holder claim or license metadata
was added. The owner's provisional preference remains provisional.

Dependency audit expanded the previous 33 queries with pnpm, the installed esbuild
platform package and 12 setuptools vendored package versions: 47 returned results, no
listed advisories. Query/response are saved in `evidence/m81/dependencies/`. The fresh
frontend lock is unchanged. Installed tools/dependencies are distinct from code bundled
into the wheel; whole-environment redistribution would require another review.

## Distribution review and proposed inventory

The snapshot inventory covered 10,678 non-cache/build files, including 10,516 evidence
files / 944,721,025 bytes and 162 source/doc/tool files / 1,752,870 bytes at scan time.
Later M8.1 reports/notices are separately recorded by the final release inventory.
No private-key, token-prefix or literal-credential-assignment pattern was found. This is
a conservative regex scan, not proof that no secret exists. It identified 47 files with
personal Windows paths and 31 with email-like strings, mostly historical reports and
public upstream metadata/notices. Values were withheld. Originals remain available locally.
The first two scans were interrupted because email matching was inefficient; the third
bounded-pattern scan completed. Incomplete attempts were not counted as clean scans.

The original Git index is unchanged. Its tracked docs/VERIFICATION.md contains a personal
path, and its staged source lacks later milestones. Ignore rules cannot remove already
tracked/staged content. Do not commit that index as a release and do not add all evidence.
Scoped ignore additions protect new local audit/operational files without deleting them.

The proposed local review distribution is generated by `scripts/prepare_m81_review.py`:

- Source, tests, workflows, manifests/unchanged locks, docs, fixtures, benchmarks and
  upstream notices, with generated production assets and declared curated UI data.
- A derived docs/VERIFICATION.md copy replaces personal absolute paths; original document
  and original/derived hashes are preserved. No scientific record is edited for privacy.
- A separate compressed archive retains unchanged M3/M4/M5/M5.1/M6 campaign data,
  including M6's full integrity closure. Individual scientific record hashes remain exact.
- Excludes Git internals, caches, environments, node_modules, downloaded dependencies,
  operational logs, profiles, local screenshots and unrelated working directories.

`work/m81-public-review/release-inventory.json` gives exact proposed paths, sizes and SHA256
values; its summary is copied into local evidence. This is a local review copy, not an
approved or published release. Source export plus full evidence archive supports review
without committing approximately 0.95 GB of raw exploratory/operational evidence to Git.
The archive includes selected campaign evidence, not every development/reproduction folder.
Public notices may retain necessary public upstream contact/copyright information.

## Fresh end-to-end and scientific integrity

Fresh non-editable 3.12 wheel + newly built frontend + declared data kit completed in
47.153 s: real counterexample 10 → 5 actions, model 1 → 5 states, 35/35 regressions,
73/100 → 100/100 frozen traces and 1967/1996 → 1996/1996 outputs. Original training:
1855 actions / 288 resets; separate original evaluation 3992 / 200. Twin training 1043 /
174; twin evaluation 3992 / 200; isolated replay 5 / 1. Frozen sequences and budgets are
unchanged. Independent twin replay and all four typed support labels passed; the
unsupported inventory adapter made zero oracle queries and is not called reconstruction.

Real browser smoke loaded the clean wheel's production assets, historical replay and
live typed preview responses from the actual backend. Ambiguous transition and subsequent
unknown-state refusal remained visible; captured console error list was empty. HTTP
verified the current admission limits and complete bundled notice bytes. The temporary
tab closed; owned server exit was verified by native process counters. No graceful
PTY shutdown log is claimed. Test/session temporary artifacts are retained for diagnosis.

Read-only audit reconfirmed 582 M6 folders, 216 cells and 324 points and reconciled the
fresh run. M3–M7 artifacts and source snapshots were not changed; only a bounded supported
demo ran. Inventory remains unsupported; rare/delayed paths remain difficult; efficiency
superiority is unproven; prior algorithms are attributed; abstention is not correct
prediction. No OS-enforced hostile-code containment or universal equivalence is claimed.

## Minimum owner actions

1. Confirm rights/holder(s) for original project material and explicitly select Apache-2.0
   after reviewing M81_APACHE_REVIEW.md and the attribution inventory. This alone does not
   authorize publication.
2. Approve the exact reviewed source/evidence inventory for selected-file staging/commit
   and a named private GitHub destination, and explicitly authorize hosted workflow runs.
   No remote exists now; creating one also needs explicit approval. This supplies actual
   Linux and physical-link results; failures must be fixed before release signoff.
3. After those gates pass, separately authorize any public publication or visibility change.

Public release cannot be approved solely by waiving unverified tests. No commit, staging,
reset, push, remote creation, PR, hosted workflow, publication, deployment or visibility
change occurred. Existing staged work is preserved; the final index hash is unchanged:
`7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D`.
