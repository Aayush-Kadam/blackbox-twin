# Third-party notices

Original BlackBox Twin contributions are licensed under Apache-2.0, Copyright 2026
Aayush Kadam. This does not relicense upstream material. LICENSE contains the official
Apache-2.0 text; NOTICE records project attribution and bundled runtime notices.
The scoped review identified no conflicting original-code ownership claim or
separate-permission exception. Existing upstream holders retain their own rights.

## Bundled browser runtime

React 19.2.0, react-dom 19.2.0 and scheduler 0.27.0 are bundled under MIT, Copyright
(c) Meta Platforms, Inc. and affiliates. Complete license text is included in
[THIRD_PARTY_LICENSES.txt](src/blackbox_twin/workbench_assets/THIRD_PARTY_LICENSES.txt),
alongside [linked legal comments](src/blackbox_twin/workbench_assets/app.js.LEGAL.txt).
Preserve both files with the JavaScript, including in installed wheels.

## Installed dependencies and build tools

[third_party/](third_party/) contains upstream texts and provenance:

- AALpy 2.0.0: MIT. Its source distribution omitted a license file; the recorded
  LICENCE.txt is explicitly a commit-pinned upstream repository fallback, not a text
  extracted from that archive. AALpy supplies the learning foundation; no new L*
  algorithm is claimed.
- pydot 4.0.1: MIT and Python-2.0 texts from its SHA256-verified source distribution,
  including terms for standard-library-derived material.
- setuptools 84.1.0: root license from its SHA256-verified source distribution.

Provenance JSON records exact sources, archive hashes and extracted-member hashes.
Python dependencies, pnpm, esbuild, Prettier and build backends are installed
dependencies/tools, not bundled Python environments or node_modules in this source
distribution. Their licenses continue to govern them. Redistributing a whole environment
or build-tool bundle requires reviewing its actual contents and preserving every
applicable notice. Metadata summaries do not replace license texts.

No third-party font, image or icon file is used in the application source: system fonts
are referenced by name, and interface graphics are project markup/styles. Prior-art
papers and sites are linked, not bundled. Local verification screenshots, operational
logs, environments and full research archives are outside the approved source inventory.

## Historical audit records

[M8 dependency review](docs/M8_DEPENDENCIES.md),
[M8.1 Apache review](docs/M81_APACHE_REVIEW.md) and dated milestone reports preserve
their original pre-approval findings. Pending licensing and missing-text statements
there are historical: the M8.2 decision and notices above supersede those gates.
See [executed validation](docs/M82_VALIDATION_RESULTS.md).
