# M8 dependency review — 2026-10-28

Final Windows 3.12 resolved runtime/development closure and build backend: 28 Python
versions plus five npm packages, **33 completed exact-version OSV queries**, zero listed
advisories for that set. This does not establish vulnerability freedom. Python 3.11's
installed inventory is saved separately; platform-conditional closure must be reevaluated
on Linux. No Linux advisory inventory or execution is claimed.

Evidence: `evidence/m8-dependencies-patched-build/{audit,osv-query,osv-response}.json`;
package-by-package direct/transitive and runtime/dev/build classification:
`evidence/m8-dependency-ledger-final/dependency-ledger.csv`. All seven original GHSA
records, affected ranges, severity vectors and references are saved in that directory.
Python metadata/Requires-Dist and copied license texts are retained with the audit.
The frontend pnpm registry audit returned no listed advisories (31 total dependencies,
including optional platform entries); saved as workspace `work/m8-npm-audit.json`.
The five npm source packages are React, react-dom, scheduler, esbuild and Prettier.
The esbuild platform binaries share its pinned version; they are not all installed here.

| Original affected dependency | Advisory | Affected range / fixed version | Applicability and disposition |
|---|---|---|---|
| Starlette 0.49.3 | [GHSA-82w8-qh3p-5jfq](https://github.com/advisories/GHSA-82w8-qh3p-5jfq) | >=0.4.1,<1.3.1 / 1.3.1 | High availability impact in advisory; form endpoint not used here. Updated to 1.10.0. |
| Starlette 0.49.3 | [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr) | <1.0.1 / 1.0.1 | Moderate URL/Host poisoning; updated plus strict pre-routing Host checks. |
| Starlette 0.49.3 | [GHSA-jp82-jpqv-5vv3](https://github.com/advisories/GHSA-jp82-jpqv-5vv3) | <1.3.0 / 1.3.0 | Request path/authority confusion; updated. |
| Starlette 0.49.3 | [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r) | <1.1.0 / 1.1.0 | High confidentiality impact, Windows StaticFiles UNC paths; static files used here, so material. Updated. |
| Starlette 0.49.3 | [GHSA-x746-7m8f-x49c](https://github.com/advisories/GHSA-x746-7m8f-x49c) | <1.1.0 / 1.1.0 | Unexpected HTTPEndpoint method dispatch; route handlers here do not use that class. Updated plus method allowlist. |
| setuptools 80.9.0 | [GHSA-h35f-9h28-mq5c](https://github.com/advisories/GHSA-h35f-9h28-mq5c) | <83.0.0 / 83.0.0 | Moderate macOS sdist exclusion issue; Windows wheel validation does not exercise that path. Pin updated to 84.1.0. |
| setuptools 80.9.0 | [GHSA-xmj3-9gf7-h52w](https://github.com/advisories/GHSA-xmj3-9gf7-h52w) | >=38.2.2,<84.1.0 / 84.1.0 | Low severity, malicious metadata in legacy Windows wheel installation; no such install path used. Pin updated to 84.1.0. |

PYSEC entries in the original lookup overlap these GHSA records; do not count them as
independent additional vulnerabilities. Original web lock and baseline audit are preserved.
Current installs use `requirements-m8-lock.txt`; do not install the historical workbench lock.
FastAPI was changed to 0.162.0 to support the patched Starlette, adding OpenTelemetry API
1.45.1. Current pytest/HTTPX compatibility emits a TestClient deprecation warning; it is
recorded rather than suppressed. AALpy also emits two invalid-escape warnings in the
3.11 suite (DeprecationWarning); the first fresh 3.12 import emitted SyntaxWarnings.

Compatibility evidence: full Python suites on 3.11/3.12, focused HTTP/path/admission tests,
production frontend build, fresh wheel build and independent installation. A version upgrade
and completed tests do not mean every upstream exploit was reproduced. No advisories remain
listed for the final queried versions, but attribution gaps and fresh frontend installation
remain release gates. An earlier recovery query failed DNS and is preserved as UNKNOWN;
it is followed by the successful normalized closure lookup, not relabelled as clean.
