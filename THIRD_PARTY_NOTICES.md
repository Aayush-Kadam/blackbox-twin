# Third-party dependency review — local draft

M8.2: the owner approved Apache-2.0 for original contributions, Copyright 2026 Aayush
Kadam, after the scoped attribution audit. This does not relicense any upstream material.
The dated M8/M8.1 status statements below are historical; current project terms are in
LICENSE and NOTICE. No additional original-code ownership claim or separate-permission
exception was identified. Existing upstream copyright holders remain credited below.

## M8.1 current attribution status

The frontend build now includes complete MIT license text for React 19.2.0,
react-dom 19.2.0 and scheduler 0.27.0 in the wheel's
`workbench_assets/THIRD_PARTY_LICENSES.txt`, in addition to esbuild's linked legal comments.
These are bundled third-party runtime code. Preserve both files with the JavaScript.

`third_party/` records upstream dependency notices: commit-pinned AALpy LICENCE.txt;
pydot 4.0.1 MIT and Python-2.0 texts from its SHA256-verified PyPI source distribution;
and setuptools 84.1.0's root license from its verified source distribution.
Provenance JSON records exact sources, archive hashes and extracted-member hashes.
AALpy's 2.0.0 sdist contains no license file; its notice is explicitly a pinned upstream
repository fallback, not represented as having been extracted from the release artifact.
The initial collector missed LICENSES/ subdirectory texts and reused basenames; that
attempt is retained locally and superseded by the path-preserving second collection.

Python dependencies, pnpm, esbuild, Prettier and build backends are installed tools or
dependencies, not vendored runtime packages in the proposed project wheel. The pydot
standard-library-derived module retains Python-2.0 terms. If distributing whole environments,
reopen license review for all transitive and vendored material. Current licensing proposal
and ownership questions: `docs/M81_APACHE_REVIEW.md`. No root project license is selected.

No third-party font, image or icon file is used in the application source: system font
families are referenced by name; the letter mark, graph and interface assets are project
markup/styles. Browser screenshots are local verification material, excluded from the
proposed public source export. Prior-art papers and sites are linked, not bundled.

The material below is the preserved M8 starting inventory; its missing-text gate is
superseded by the M8.1 collection and provenance described above.

## Historical M8 inventory

This is an attribution inventory, not the project's license or a declaration that all
redistribution obligations have been discharged. Exact resolved versions, metadata and
copied installed license/NOTICE files are in
`evidence/m8-dependencies-patched-build/audit.json` and its `licenses/` directory;
`evidence/m8-dependency-report/dependency-ledger.csv` distinguishes direct/transitive use.

AALpy supplies the active automata learning foundation; no novel L* algorithm is claimed.
Its installed metadata identifies MIT, but its installed wheel did not supply a license
file discovered by the audit. pydot likewise reports MIT without an installed license
text found. These upstream texts/attributions require completion before redistribution.
Other metadata includes MIT, BSD variants, Apache-2.0, PSF-2.0, and certifi's MPL terms.
Keep each dependency's full actual notices rather than replacing them with this summary.

React/react-dom/scheduler browser code is bundled with esbuild's linked legal comments
in `src/blackbox_twin/workbench_assets/app.js.LEGAL.txt` (included in the wheel).
The audit also copies npm package LICENSE files under `licenses/npm/`. esbuild and
Prettier are development tools, not browser runtime modules. Platform-specific optional
esbuild packages are recorded in the pnpm lock and registry audit.

OpenTelemetry API uses Apache-2.0; preserve its actual installed LICENSE/NOTICE.
Packaging is dual-licensed Apache-2.0 OR BSD-2-Clause. Do not infer a license merely
from the absence of a machine-readable expression. The build backend also needs its
upstream license text included in any redistributed build-tool bundle.

No dependency binaries, Python runtime, or node_modules are approved for public release
by this local audit. Before any public artifact, close upstream attribution gaps and
inspect the actual final archive. Project terms remain owner-selected.
