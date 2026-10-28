# M5.1 verification — 2026-10-27

**Engineering: PASS in the declared bounded wallet class. M6: READY WITH LIMITATIONS.**
Support metadata, full bounded ambiguity detection, concrete fallback, state poisoning,
real distinguishing probes and separate correctness/coverage metrics are implemented.
This is not a claim of superior fidelity through abstention, nor proof that arbitrary
software belongs to the model grammar. M6 has not started. M4 and M5 historical verdicts
and measurements remain unchanged.

Read `M5_1_DIAGNOSIS.md` for the complete B autopsy and `M5_SUPPORT_POLICY.md` for exact
status/grammar/runtime semantics. Implementation: `support.py`, `support_runtime.py`,
`m51.py`, version-3 synthesis dispatch and the new `typed-harden` CLI. Existing StatePrefix
defaults, old typed commands, finite/guarded model formats and M3 refinement remain intact.

## Fresh protocol and isolation

`benchmarks/manifests/m5-1-fresh.json` froze policy/source hashes, fixture fingerprint,
budgets, value split and seeds before evaluation. Raw frozen source is preserved at
`evidence/m5-1-fresh/source-snapshot/`. Target seed 61101, probe seeds 71101/71102,
evaluation sequence seed 81101, and unchanged legacy StatePrefix seed 5101 are separate.
Two configurations were drawn without replacement from a preregistered pool excluding
M5's development/evaluation configurations. Both happened to have balance cap 1:
fresh-0 limit 2, fresh-1 limit 1. They were retained, not replaced with easier or broader
cases after seeing results. This is a six-training-cell focused sprint, not M6.

New reserved amounts are -7,-5,-3,3,6,7; amount 2 is permitted. This is an explicit new
experimental split, not a rewrite of M5's reservation of amount 2. Thirty seen and thirty
unseen sequences are frozen before all training, identical within paired comparisons.
Their 218/215 action outputs are scored separately. Each pair also receives 136 exhaustive
reachable state/transaction cases and 28 validation cases after training; 224 cases total.
Original reference acquisition happens only after all three training arms return.

All arms share the initial fixed-grid L*/native StatePrefix phase, observable-state
completion, isolated physical processes/caches and 5,000-action/1,000-reset/120-s ceiling.
The old adaptive arm retains its real differential search/shrinking/probing/refitting.
The hardened arm starts from the fixed-grid seed, then executes at most 12 full-space
ambiguity probes and replays all its observed contextual regressions. Different stopping
and regression obligations remain visible in costs; equal ceilings are not equal spending.
No private configuration, original source or evaluation outputs are passed to inference.

## Main comparison

| Configuration / method | Unseen exact traces | Unseen exact outputs | Output coverage | Conditional output accuracy | False-supported rate | Abstention |
|---|---:|---:|---:|---:|---:|---:|
| fresh-0 fixed grid | 22/30 | 161/215 | 74.884% | 100% | 0% | 25.116% |
| fresh-0 original adaptive | 22/30 | 161/215 | 74.884% | 100% | 0% | 25.116% |
| fresh-0 hardened | 22/30 | 161/215 | 74.884% | 100% | 0% | 25.116% |
| fresh-0 old adaptive + policy only | 22/30 | 161/215 | 74.884% | 100% | 0% | 25.116% |
| fresh-1 fixed grid | 22/30 | 161/215 | 74.884% | 100% | 0% | 25.116% |
| fresh-1 original adaptive | 30/30 | 215/215 | 100% | 100% | 0% | 0% |
| fresh-1 hardened | 30/30 | 215/215 | 100% | 100% | 0% | 0% |
| fresh-1 old adaptive + policy only | 30/30 | 215/215 | 100% | 100% | 0% | 0% |

Output fidelity is 74.884% or 100% as the exact numerators show; trace fidelity is
73.333% or 100%. Sequence coverage equals those trace rates here; conditional complete
trace accuracy is 100%. These are different denominators and are all present in JSON.
All seen groups match 30/30 traces and 218/218 outputs. All validation groups match
28/28 traces and 84/84 outputs. Legacy concrete outputs are their implicit support claim,
not retroactive OBSERVED/INFERRED_SUPPORTED metadata.

| Configuration / method | Exhaustive exact contextual traces | Exhaustive exact outputs | Output coverage |
|---|---:|---:|---:|
| fresh-0 fixed grid | 124/136 | 384/408 | 94.118% |
| fresh-0 original adaptive / hardened / policy-only | 132/136 each | 400/408 each | 98.039% |
| fresh-1 fixed grid | 124/136 | 384/408 | 94.118% |
| fresh-1 original adaptive / hardened / policy-only | 136/136 each | 408/408 each | 100% |

Guard acceptance precision/recall are **1.0/1.0 in every fresh arm**, over 136 transactions
per configuration, with abstentions treated as non-acceptance. There are only two accepted
transaction points per configuration in these cap-1 populations. Conditional output accuracy
is 100% and false-supported rate is zero in all measured fresh groups, including the
legacy arms. This fresh sample therefore shows no safety-rate or fidelity advantage
over original adaptive; it validates honest support behavior, not a new performance win.
The historical development cases separately demonstrate removal of two wrong concrete
error classifications. The sampled fresh cap-1 systems chiefly test rejection/error
generalization; they do not establish fresh unseen-valid arithmetic success at larger caps.

The irreducible fresh-0 ambiguity is informative: amount 3 is withheld. Limits 2 and 3
produce identical behavior at all other permitted transaction values, while differing
at 3. The compiler preserves that possibility instead of using the private generation
pool to discard the alternative. The generated twin abstains and then keeps unknown
state until reset. These cases remain failures in end-to-end fidelity.

## Component separation

The policy-only arm converts original adaptive observations with no new learning calls.
It has the same fresh-case coverage as the final hardened arm. Its training data differ
from the hardened seed, so do not attribute their equality to probe quality alone.

A separately labelled **post-hoc component diagnostic** executes hardened revision-000
before resolution, using the same already frozen references. It is not another independent
confirmatory comparison and did not guide training. `evidence/m5-1-component-check/`:

- Before probes: 8/30 unseen traces, 79/215 outputs (36.744% coverage), and 112/136
  exhaustive contextual traces for each configuration. Conditional concrete accuracy stays 100%.
- After 9/6 probes respectively: 22/30 and 30/30 unseen traces, with the main-table coverage.

This demonstrates real affordable ambiguity resolution restoring coverage rather than
calling abstention improved fidelity. The check makes no original oracle calls; its
1,850 twin actions / 448 resets are separate from primary totals.

## Physical costs and regressions

| Configuration / method | Original training actions | Resets | Distinguishing probes | Observed regressions | Local wall seconds |
|---|---:|---:|---:|---:|---:|
| fresh-0 fixed grid | 1,000 | 384 | n/a | n/a | 0.713 |
| fresh-0 original adaptive | 1,629 | 508 | legacy boundary procedure | 88/88 | 1.622 |
| fresh-0 hardened | 1,233 | 456 | 9 | 61/61 | 2.512 |
| fresh-1 fixed grid | 1,000 | 384 | n/a | n/a | 0.671 |
| fresh-1 original adaptive | 1,619 | 506 | legacy boundary procedure | 87/87 | 1.587 |
| fresh-1 hardened | 1,223 | 450 | 6 | 58/58 | 2.030 |

All six training cells completed. Costs include independent seed learning, reset checks,
all probe/access actions, old adaptive shrinking/refinement and each arm's regression
replays. Hardened seed costs are not reused free from the baseline arm. Primary original
training is **7,704 actions / 2,688 resets**, below the preregistered 30,000-action maximum.
Shared original evaluation is **1,850 / 448** separately, hence **9,554 / 3,136** original
calls including evaluation. Primary twin calls total **10,854 / 2,598** separately.
Development, historical diagnostic replay and installed reproduction are not pooled into
these learning numerators. Timings are local single runs; full-space computation is
slower here despite fewer total physical calls than original adaptive. No general query
efficiency or runtime superiority is claimed from two small configurations.

## Tests, audit and reproduction

Baseline revalidation: **111 passed, zero failed in 139.07 s**. Full M0–M5.1 suite:
**130 passed, zero failed in 144.85 s**, `evidence/m5-1-pytest.txt`. Final focused suite:
19 passed in 7.92 s, including strengthened same-value/different-state standalone and
hardened forbidden-file-read checks.
Earlier assertions were retained. Lint and formatting pass; no static type checker is configured.

The 19 focused cases cover all feasible threshold cuts, missing boundary support,
multiple compatible guards, per-state applicability, update disagreement, typed invalid/
out-of-domain inputs, unrepresentable/nonconvex classes, overlapping/missing guards,
contradictory observations, physically charged resolution, exhausted action budget and
zero probe cap, unknown-action cascades, reset recovery, serialization/provenance and
separate accuracy/coverage denominators. Plain/explained generated twins run in isolated
Python with package loading disabled. Existing timeout/crash/Windows cleanup tests remain.

`scripts/audit_m5_1.py` reports PASS: source/fixture hashes, all SQLite training/evaluation
counts, reserved-value exclusion, zero full-word overlaps in both seen/unseen frozen groups,
freeze-before-training, complete support-model recompilation, physical evidence references,
independent concrete/coverage/abstention metric recounts, guard precision/recall, standalone
runtime equivalence and all observed regressions. Artifacts: `evidence/m5-1-audit.json`.
Historical M2, M3 and M5 audits were reexecuted successfully without changing their data;
M4 remains reproducible from its frozen source and its negative verdict is unchanged.

Offline non-editable installation succeeded. A fresh-0 hardened learning cell reproduced
**1,233 actions / 456 resets**, identical semantic model ID, support cells and regressions.
The generated twin was copied alone into an otherwise empty directory and executed with
`python -I -S`, in plain and `--explain` modes. Both reproduced all **224 policy cases /
925 actions / 224 resets per mode**, including all four support statuses. This verifies
the *same policy outputs including abstentions*, not 100% target fidelity. Only one cell
was independently repeated; receipt: `evidence/m5-1-reproduction/summary.json`.

## Reproduction commands

From the enclosing workspace; use fresh output directories, workspace-owned TEMP/TMP
and UV_CACHE_DIR for tests/offline installation. The frozen protocol already exists.

```powershell
work/.venv/Scripts/bbt.exe typed-harden --protocol outputs/blackbox-twin/benchmarks/manifests/m5-1-fresh.json --out <fresh-output>
work/.venv/Scripts/python.exe outputs/blackbox-twin/scripts/audit_m5_1.py --suite outputs/blackbox-twin/evidence/m5-1-fresh
uv pip install --offline --python work/clean-venv/Scripts/python.exe --reinstall-package blackbox-twin outputs/blackbox-twin
work/clean-venv/Scripts/python.exe outputs/blackbox-twin/scripts/reproduce_m5_1.py --suite outputs/blackbox-twin/evidence/m5-1-fresh --out <fresh-reproduction-output>
work/.venv/Scripts/python.exe -m pytest outputs/blackbox-twin/tests -q --basetemp=<fresh-test-folder>
work/.venv/Scripts/python.exe -m ruff check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
work/.venv/Scripts/python.exe -m ruff format --check outputs/blackbox-twin/src outputs/blackbox-twin/tests outputs/blackbox-twin/scripts outputs/blackbox-twin/fixtures
```

Installed CLI use requires `--project` pointing to the source project containing the
owned fixture. Source hashes intentionally reject later modified algorithms against this
protocol. No commit, push, release, new dependency, solver or external service was added.
The staged tree remains `9d804578899a21849533231252b1a2fbb7e23059`.

## M6 readiness

**READY WITH LIMITATIONS:** correctness versus coverage is measurable; known ambiguity
does not become an unsupported concrete guess; generated-state consistency survives
refusal/reset; support provenance and fresh evaluations reproduce. Perfect held-out
fidelity is not required to benchmark a model honestly.

Restrictions: fixed finite wallet domain; observable-state sufficiency; discovered output
vocabulary; three-term linear guard language and restricted updates; conservative independent
class spaces; no general symbolic references/hidden registers; limited fresh cap-1 coverage;
no statistical performance claim or live learner interruption recovery. M6 should measure
larger permitted balance caps, model-class violations, conditional accuracy and coverage
jointly, and distinguish infrastructure failures from abstentions. This is a readiness
recommendation only: **no broader M6 campaign was started**.
