# M7 — local scientific workbench

**Engineering PASS WITH LIMITATIONS.** M7 implements the originally specified React /
FastAPI interactive workbench. The roadmap and original master-build specification called
for this stack, real experiment exploration, learned-state visualization, differential
comparison, counterexamples, query costs, twin export and a live flow. There was no scope
conflict with the continuation prompt. This is an extension of the CLI, not a replacement.

## Start here

Commands below run from the workspace root containing `outputs/blackbox-twin` and `work`.
The verified project environment already has the optional dependencies installed:

```powershell
work/.venv/Scripts/python.exe -m blackbox_twin.workbench --project outputs/blackbox-twin --runs outputs/blackbox-twin/runs/m7-live --port 8765
```

Open **http://127.0.0.1:8765/**. No frontend development server, GPU, paid API, cloud account
or browser package download is needed. The React bundle and styles ship in the Python
package; the FastAPI server binds only to loopback. This command keeps the server in the
foreground. Let any active demo finish, then stop it with Ctrl+C.

1. **Discover & refine** opens the clearly labelled historical M3 replay. Inspect the
   public JSON action interface, initial one-state hypothesis and recorded 10-action
   counterexample. Switch to its five-action minimized witness; the highlighted fifth
   step shows the original accepting commit while the initial twin denies it.
2. Switch **Revision 0 / Revision 1**, select learned states and inspect their real outgoing
   transitions. Download model JSON or the independently executable twin. Finite legacy
   predictions are not relabelled as version-3 evidence-aware support.
3. Choose **Run fresh demonstration**. This executes the original owned delayed fixture,
   AALpy learning, real differential search, replayed deletion minimization, automatic
   refinement, twin regeneration and regression replay. It then evaluates separately on
   100 input sequences frozen before learning. It is not a prerecorded animation.
4. On completion, the explorer selects the new experiment. The recorded stop reason,
   physical original/twin costs, configuration, seed, model hashes, paired evaluation,
   counterexamples and paginated SQLite events can be inspected. No percentage-progress
   estimate or fabricated intermediate result is displayed.
5. **Support & uncertainty** reads a real M6 wallet model. Choose OBSERVED,
   INFERRED_SUPPORTED, AMBIGUOUS or UNSUPPORTED, then inspect its predictions. The unsupported
   example first attempts an ambiguous deposit and then a balance check: both refuse,
   because state is unknown. Append reset + balance check to observe recovery.
6. **Benchmark evidence** exposes all 324 M6 scored checkpoints. Filter track C to see
   inventory incompatibility and budget stops, zero coverage, undefined conditional
   accuracy shown as `—`, and criterion failures. Costs and provenance are expandable.

Typed previews are **saved-policy evaluations with zero new original-oracle queries**.
Every preview starts from reset. Metadata includes model/rule IDs, real observation
references, supported update alternatives and reasons. Evidence rows are capped at 20
per prediction; total and truncation are explicit. Preview output is never presented as
a fresh target measurement. Public contract validation errors differ from unknown effects.

## Reproduce the flagship without the browser

Use a fresh output directory; existing experiments are never overwritten:

```powershell
work/.venv/Scripts/python.exe -m blackbox_twin.m7_demo --project outputs/blackbox-twin --out outputs/blackbox-twin/runs/my-m7-demo
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m7.py --project outputs/blackbox-twin --run outputs/blackbox-twin/runs/my-m7-demo
```

The target, seeds and limits are fixed by the demonstration wrapper. Learner seed 7,
evaluation seed 20261027; training at most 6,000 original actions / 2,000 resets / 90 s,
evaluation separately at most 6,000 / 1,000 / 90 s. Per-query timeout is 2 s; sequences
are capped at 100. The isolated final-twin replay has its own 10-s subprocess timeout.
These are session limits, not a verified OS process-tree or memory containment policy.

The initially weak equivalence search is deliberate: it lets a real learner miss a
history that differential discovery can subsequently reveal. It does not inject a fake
transition or manually fabricate a defective model. The original M3 workflow remains
unchanged. Its differential random search is not a replacement for the native StatePrefix
`bbt learn` default, and no custom-ranker performance claim is made.

## Installation and frontend development

For a separate Python environment, install the existing core/dev lock and the new verified
workbench lock, then the local project. `requirements-workbench-lock.txt` includes the
versions used in verification; it does not replace the historical core lock.

```powershell
uv venv --python work/.venv/Scripts/python.exe work/my-m7-env
uv pip install --python work/my-m7-env/Scripts/python.exe -r outputs/blackbox-twin/requirements-workbench-lock.txt
uv pip install --python work/my-m7-env/Scripts/python.exe --no-deps outputs/blackbox-twin
```

Alternatively, the optional extras are `[workbench,workbench-test]`; `workbench-test`
provides HTTPX for transport tests. Core use does not import FastAPI. The clean verification
used a new environment and a non-editable wheel installation, not the source-tree import.

To rebuild or test the React interface, use Node and pnpm from the frontend directory:

```powershell
cd outputs/blackbox-twin/frontend
pnpm install --frozen-lockfile --ignore-scripts --store-dir .pnpm-store --node-linker hoisted
node build.mjs
node test.mjs
pnpm format:check
```

Pinned React / React DOM 19.2.0, esbuild 0.25.10 and Prettier 3.6.2 are recorded in the
lockfile. The project-contained store and hoisted layout avoid the Windows global-store
registration symlink failure encountered here. Installation scripts were not enabled;
the platform esbuild executable supplied by its optional package built successfully.
No CDN is contacted by the running page. Reinstall the Python package after rebuilding
if testing a non-editable installed copy. The bundled JS is 220,416 bytes and CSS 12,251
bytes in the verified build; these are asset sizes, not runtime-memory measurements.

## Scope and remaining limits

Only the owned delayed-commit fixture can be launched through the workbench. Clients
cannot choose an executable, upload a program, change budgets/seeds or execute remote
targets. Runs receive fresh IDs, one worker executes at a time, and concurrent requests
receive a conflict. Historical evidence is read-only, with allowlisted IDs and checked
model/twin hashes. Live output roots beneath historical `evidence/` are rejected.

The server validates Host, rejects cross-origin mutation, requires a local request header,
caps JSON bodies at 32 KiB and typed previews at 30 requests, and serves a restrictive
content-security policy. This is a local trusted-fixture workbench, not a multi-user
authenticated service or an OS-enforced sandbox. Same-user filesystem/network rights,
Windows Job Objects, hostile program containment, forced termination during active work
and peak memory have not been established as security guarantees. No cancel button is
offered; shutdown waits for bounded work through the application lifecycle.

M6 remains unchanged: finite rare/delayed failures, wallet coverage loss, unsupported
two-counter inventory and lack of query-efficiency superiority all remain visible.
Neither abstention nor a successful isolated replay proves target reconstruction.
The fresh demo's 100/100 refined sample traces do not prove universal equivalence.

M8 readiness is **READY WITH LIMITATIONS** for the established hardening work. Outstanding
M8 gates include cross-platform checks, broader security/dependency/license review,
profiling and release preparation. M7 browser verification was desktop-only; no independent
usability study or accessibility certification was performed. Current CI predates the
optional workbench extras; its workbench/frontend coverage must be wired and verified in
M8. No M8 implementation, commit, publication, remote resource or public deployment occurred.

See [M7 verification](M7_VERIFICATION.md), [M6 findings](M6_RESULTS.md) and the
[version-3 support policy](M5_SUPPORT_POLICY.md).
