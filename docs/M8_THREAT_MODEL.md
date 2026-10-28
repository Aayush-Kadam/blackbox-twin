# M8 local workbench security review

Scope: a single operator inspecting owned synthetic fixtures and trusted saved artifacts,
on loopback. This is not an execution sandbox, hosted service, multi-user product, or
safe way to execute an adversary's program. Use only targets you own or are authorized to test.
Generated twins are hypotheses; finite testing does not prove universal equivalence.

| Finding | Impact / severity in intended scope | Remediation / evidence | Remaining boundary |
|---|---|---|---|
| Artifact paths could resolve outside their declared root | High if artifact paths are manipulated | Resolve containment for replay/live/typed/export paths; exact revision filenames; fixture executable containment; traversal and integrity regressions | Four physical symlink/junction tests unavailable on this host. Blocking broader path-security signoff until actual execution on a permitted host. Trusted same-user artifacts can still race resolution/open. |
| Oracle inherited the entire operator environment | High if untrusted target executed | Explicit OS/locale allowlist: SystemRoot, WINDIR, PATH, TEMP, TMP, LANG, LC_ALL, TZ. Real child test checks synthetic secret and PYTHONPATH absent without printing values. | PATH/temp remain trusted operator configuration; inherited OS handles/filesystem/network are not isolated. |
| Repeated browser demonstrations could accumulate work | Moderate local exhaustion | Single worker; concurrent rejection 409; three admissions per output root, persistent across restart; 64 MiB storage admission; at most 10,000 inspected entries; linked storage rejected. Tests cover busy/restart/storage/failure. | Admission is not a disk, RAM, or process-tree OS quota. A new output root deliberately starts a new allowance. |
| Host/body trust and verbose errors | Moderate local request abuse | Strict Host/port grammar before request URL use; GET/HEAD/POST only; same-origin POST plus local header; no CORS; bounded content length AND received bytes; two-second body deadline; 64-level JSON nesting ceiling; malformed JSON rejection; sanitized API errors; CSP/nosniff/no-store. | Local malware can send authorized requests. No authentication or remote service guarantee. |
| Affected web/build dependencies | See advisory ledger | Starlette 0.49.3 → 1.10.0, compatible FastAPI 0.162.0; setuptools 80.9.0 → 84.1.0. Exact advisories and versions preserved. | Advisories are a dated query, not proof of vulnerability absence. |

`tests/test_m8_security.py` exercises these changes; `tests/test_workbench.py`,
`test_adversarial.py` and `test_cleanup.py` retain action/reset budgets, normal execution,
crashes, deadlines, oversized responses and injected Windows sharing failures.
Logical tests do not substitute for the four skipped physical link/junction cases.

The server binds 127.0.0.1, disables proxy-header trust, caps request concurrency/backlog
at 16, and waits for its bounded worker on ordinary shutdown. No public listener is
authorized. Forced termination and adversarial descendant cleanup are not guaranteed.
The adapter's response timeout does not establish a deadline for every possible blocking
stdin write to a hostile non-reading child. Generated twins read standalone JSON lines
from trusted callers; their stdin is not an independently enforced request quota.
These limitations preclude hostile-code execution claims.

SQLite is opened read-only for views; model hashes detect accidental corruption, not
malicious replacement of both data and hashes by the same user. No pickle/eval model
loader or uploaded executable endpoint is introduced. Generated code embeds structured
data and fixed interpreter helpers. Existing scientific contracts and learning strategy
defaults remain unchanged; current oracle environment hardening is recorded separately
from frozen historical source snapshots.

Dependency sources and detailed affected/fixed ranges are preserved in
`evidence/m8-dependency-report/`. The old web dependency lock is historical and must not
be used for current installation. No credentials were required for advisory queries.
