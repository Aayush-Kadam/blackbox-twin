# M5 readiness — design only, 2026-10-27

Historical pre-implementation design. M5 has since been implemented and evaluated;
current results and limitations are in `M5_VERIFICATION.md` and `M5_EXPERIMENTS.md`.
The original readiness assessment below is preserved as design history.

M4.1 selects native AALpy StatePrefix for supported finite-state CLI learning. The custom
ranker remains an experimental baseline. **Ready for a bounded M5 implementation task;
M5 is not implemented or verified.** Typed guards and symbolic references require new
contracts and semantics, not extra action names alone. No new method novelty is claimed.

## Existing foundation and necessary changes

| Area | Reuse | Required M5 interface/change |
|---|---|---|
| Typed operations | `Action.arguments` already stores JSON | Add explicit per-operation schemas for bounded integers, strict Boolean, enum, optional missing versus null, range/type errors. Python bool must not pass integer validation. Version schemas. |
| Alphabet abstraction | Finite action-to-concrete-template map, L*, StatePrefix | Introduce versioned partitions and a mapper from abstract symbols to concrete representatives; record both. Do not equate representative fidelity with whole-partition fidelity. |
| Boundary experiments | Real reset/replay sessions and limits | Probe adjacent values around candidate splits with separate physical accounting. State-dependent thresholds require access-path contexts; cap finite domain, split count, queries and hypotheses. |
| Guard hypotheses | Neutral deterministic transition model | New model version for typed predicates, observed support and unknown regions; reject overlapping ambiguous guards. Never emit unsupported universal guards from a few agreeing samples. |
| Output behavior | Exact JSON observation comparison | Explicitly define allowed argument-dependent outputs. Begin with finite outputs; output arithmetic/copy expressions need separate supported templates and verification. |
| Symbolic references | Stored traces and reset semantics | Define bind/use/fresh/missing/wrong-type/lifetime rules, reset-scoped environments and concrete resolution. Recorder must preserve symbolic requests plus actual resolved values without silently treating variable names as literal data. |
| Cache | ReplayCacheSUL, nondeterminism detection | Key by contract/abstraction version plus concrete resolved trace or validated canonical binding context. Invalidate/replay after splits. Never merge two concrete values solely because the current partition predicts agreement. |
| Counterexamples | Replay confirmation and local ddmin | Add typed value shrinking, binding-aware dependency preservation, state/context replay and partition refinement. Current symbolic-reference rejection is intentional and must stay until semantics exist. |
| Twin export | Local dependency-free interpreter | Add typed dispatcher, nonoverlapping guard evaluation, validated reference environment and explicit unknown/unsupported outputs. Preserve old finite model interpreter. |
| Evaluation | Frozen post-training original/twin comparisons | Freeze disjoint concrete values and boundary neighborhoods per state context. Report schema/value/context coverage, exact trace fidelity, unknown rate and physical costs separately. No training feedback from held-out values. |
| Storage/recovery | Append-only events/artifacts, committed physical calls | Add versioned mapper/guard/binding provenance. Preserve raw evidence through model revisions and abstraction splits; test interruption and mismatched schema versions. |

Changing only candidate ranking cannot solve these representation requirements. A
deterministic concrete target can appear nondeterministic under a coarse mapper; do not
disable nondeterminism checks to hide this. Refine or return unsupported. Equality of
reference identity, semantic equality and output redaction must be explicitly distinct.

## Research and tool review

Primary sources checked on 2026-10-27:

- [LearnLib](https://learnlib.de/) lists AAAR and L* variants and cites work on state-local
  alphabet abstractions and extended finite state machines. Alphabet refinement and
  state-conditioned abstraction are established approaches, not a new BBT invention.
- [Tomte's own description](https://tomte.cs.ru.nl/) places a mapper between learner and
  SUT, refines abstractions when they introduce nondeterminism, and supports a restricted
  class of register automata including fresh outputs. Its restrictions matter; arbitrary
  data-bearing programs are not automatically supported.
- [RALib](https://github.com/LearnLib/ralib) provides register-automata learning algorithms.
  The primary [SL-lambda paper](https://arxiv.org/abs/2401.14324) describes learning data
  relations with a tree-based algorithm and restricted tests. Register learning is a
  distinct model/teacher problem; it is not obtained by adding reference strings to
  Mealy input templates.

Recommendation: retain the Python finite learner and implement a deliberately bounded,
inspectable mapper first. Compare its conceptual contracts with LearnLib/Tomte. Evaluate
whether RALib is needed only if reference equality/data flow exceeds that mapper's scope;
Java adapters and tool restrictions add integration work. No tool was installed or
claimed integrated during M4.1. No Z3, hypothesis committee or invented information gain.

## Proposed first local target and stopping gates

Use a fully owned deterministic resettable bounded wallet: balance 0–4, `deposit(amount)`
and `withdraw(amount)`, integers limited to -8..8, finite accepted/denied/error outputs.
This gives static validation boundaries and a state-dependent withdrawal guard without
unbounded arithmetic or output identities. Keep known evaluator tables separate from
learner inputs. Start with integer partitions plus strict schema validation; extend the
same small target to Boolean/enum/optional arguments only after the integer gate.
Symbolic references are a subsequent explicit sub-gate in M5, not a promise of the first
slice. The complete intended M5 scope remains larger than this first slice.

Before coding, freeze the concrete domain, partition representation, allowed guards,
unknown semantics, target/selection/evaluation seeds and a small physical cap (proposed
5,000 training actions, 1,000 resets, 60 s, at most 16 partition splits and 100 hypotheses).
Use StatePrefix on abstract finite symbols as the established exploration baseline;
compare fixed representative enumeration under identical physical limits. The initial
objective is correct typed behavior and boundary coverage, not a new efficiency win.

Acceptance: strict argument validation; adjacent-to-boundary and state-context checks;
concrete replay reconciliation; no cache aliasing after splits; exact standalone-twin
behavior for the explicitly supported domain; honest unknowns elsewhere; preserved M0–M4
tests; evaluator isolation; versioned evidence and repeatable install. Exhaustive finite
domain checks by the evaluator are feasible for this target and should complement frozen
held-out representative checks. They must not feed splits back into the training run.

Stop on the stated cap, repeated inconsistent abstraction, inability to represent a
guard, or unsound binding/cache semantics. Report unsupported behavior rather than
escalating to an unrestricted symbolic-learning campaign. Do not describe bounded guard
agreement as source reconstruction or arbitrary-program equivalence. M5 requires its own
implementation authorization and verification; this readiness document satisfies neither.
