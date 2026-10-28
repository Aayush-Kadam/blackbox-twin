# Local review and reproduction

Requirements: Python 3.11 or 3.12, verified on Windows and Ubuntu,
and trusted owned fixtures/data. Node is required only to rebuild the frontend; production
assets are already bundled in the Python wheel. Python imports do not require Graphviz
for the tested flows. Node/pnpm frontend tooling needs its pinned dependency registry or
an explicitly supplied package cache. No API keys or credentials are needed.

Run these commands from the repository root. `python` must select the intended interpreter.
The standard installation route is:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-m8-lock.txt
.venv/Scripts/python.exe -m pip install .
.venv/Scripts/python.exe -m blackbox_twin.cli --help
.venv/Scripts/python.exe -m blackbox_twin.workbench --project . --runs runs/local-review --port 8765
```

Open `http://127.0.0.1:8765/`. Wait for active work to finish, then stop with Ctrl+C.
The CLI's module form avoids a PowerShell launcher/redirection issue observed with one
fresh environment. The workbench needs the declared evidence data in this repository;
installing a wheel alone does not include the historical benchmark corpus.
Three fresh demos are allowed per selected output root; storage admission is 64 MiB,
not an OS disk/memory quota. Outputs are preserved, including partial failures.

The verified M8 fresh-install route used uv to build and install a non-editable wheel
into a newly created environment, with explicitly declared cached dependency downloads.
Cache availability made that install offline; runtime reproduction itself uses neither
the cache nor the original checkout. The equivalent review workflow, with uv installed:

```powershell
uv build --wheel --out-dir review/wheelhouse
python scripts/build_m8_kit.py --project . --out review/kit
uv venv review/venv --python 3.12
uv pip install --python review/venv/Scripts/python.exe -r requirements-m8-lock.txt review/wheelhouse/blackbox_twin-0.1.0.dev0-py3-none-any.whl
review/venv/Scripts/python.exe -I scripts/reproduce_m8.py --kit review/kit --out review/reproduction
```

Use fresh output paths; scripts refuse to overwrite an existing experiment. The data kit
is a hash-listed curated subset (~5.8 MB): M3 replay, M6 aggregates and one typed wallet
policy. It is not the full M6 integrity closure. The clean test copies `reproduce_m8.py`
beside the kit and installs only the wheel plus declared dependencies; the original source
tree is not on its import path. Full historical audit remains a separate repository check.
The owner approved Apache-2.0 in M8.2; preserve separate upstream notices with any copy.

Python developer checks (install `.[dev,workbench,workbench-test]` first):

```powershell
python -m pytest -vv -o faulthandler_timeout=120
python -m ruff check src tests fixtures scripts
python -m ruff format --check src tests fixtures scripts
```

Frontend source workflow, from `frontend/`:

```powershell
pnpm install --frozen-lockfile --ignore-scripts
node test.mjs
node build.mjs
node node_modules/prettier/bin/prettier.cjs --check src tests *.mjs index.html package.json
```

M8.1 verified an empty frontend/store installation using pnpm 11.25.0 and the unchanged
lockfile. The local pnpm-workspace.yaml selects hoisted packages, copied imports and a
project-local store, so the install does not need pnpm's external project-registration
symlink. No system policy changed. Tests/build/format and installed-backend browser
communication passed. M8.2 executed Windows/Ubuntu Python 3.11/3.12 and
frontend checks on both OSes: all six jobs passed on a6c8a1053fab3441586795b733b707a616e4f5b5.
See [executed results](M82_VALIDATION_RESULTS.md). Physical link tests are required
in CI (BBT_REQUIRE_PHYSICAL_LINKS=1); unavailable creation fails rather than quietly skips.
All seven physical-link cases passed with zero skips in every Python matrix job.
macOS and Python 3.13+ are outside the verified compatibility claim despite the
package's lower-bound metadata. On Ubuntu, use .venv/bin/python in place of
.venv/Scripts/python.exe throughout the examples above. The full M6 audit command
requires the separately preserved research archive; the curated source kit alone
does not contain that closure inventory.

The benchmark uses frozen held-out inputs, separate training/evaluation query accounting
and preserved failures; consult `M6_BENCHMARK_PROTOCOL.md`, `M6_RESULTS.md`,
`M6_FAILURE_ANALYSIS.md` and `PRIOR_ART.md`. Inventory inference remains unsupported,
the custom ranker underperformed, and query-efficiency superiority is unproven.
Use source snapshots for historical exact reproductions; M8's hardened environment
handling is an intentional current-code change, not a rewrite of historical results.
