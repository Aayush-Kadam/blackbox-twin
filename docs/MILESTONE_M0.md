# M0 — Feasibility, prior art and architecture

**Gate: PASS WITH LIMITATIONS.** Supported scope, oracle protocol, integration choice,
risks and testable project skeleton are explicit. No novelty or release-readiness claim.

Objective: freeze a practical deterministic finite-Mealy setting before custom algorithms.
Implemented: strict versioned contracts, Python packaging, local repository initialization,
focused primary-source review, architecture, risk register and initial evaluation protocol.
Changed files: `pyproject.toml`, `.gitignore`, `requirements-lock.txt`, `README.md`,
`src/blackbox_twin/contracts.py`, `docs/PRIOR_ART.md`, `docs/MODEL_SPEC.md`,
`docs/ARCHITECTURE.md`, `docs/BENCHMARK_PROTOCOL.md`, `docs/LIMITATIONS.md`,
`docs/ROADMAP.md`, `.github/workflows/ci.yml`.

Decisions: use installed AALpy 2.0.0 rather than implement L*; fixed concrete action
templates; JSON payload equality; local subprocess interactions; SQLite provenance;
defer Z3, HTTP and UI. Current scope does not need an LLM, GPU or paid infrastructure.

Verification: environment/package inspection, official repository and paper review,
strict contract tests, clean non-editable installation, lint/format and complete final
suite (**24 passed**). Exact commands and paths are in `VERIFICATION.md`; evidence logs
are in `evidence/`. There is no comparative M0 benchmark.

Limits/risks: the prior-art audit is focused, not exhaustive; memory inventory unavailable;
project license undecided; no Git commit because author identity is unset. Next milestone:
M1 (implemented and verified in this session; see its report).
