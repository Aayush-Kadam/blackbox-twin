# Focused prior-art audit

Checked 2026-10-27. This is a foundation audit, not an exhaustive novelty search.
No algorithmic novelty is claimed. Official documentation, repository code and primary
papers are the sources below. Absence from a README is not evidence of missing capability.

| System | Target/model | Queries, counterexamples and caching | Data/typed inputs | Execution, reproducibility and UI | Relationship to this build |
|---|---|---|---|---|---|
| [LearnLib](https://learnlib.de/) | Java framework; DFA, Mealy, Moore and other model classes | Active/passive algorithms, L*, counterexample analysis, conformance and search-based oracles, SUL adapters and caches | Alphabet abstraction/refinement is listed; data-oriented learning also exists in the broader ecosystem | Maven libraries, examples, import/export; not reviewed as a standalone workbench | Established inference and testing foundations; no claim of missing executable-model support |
| [AALpy](https://github.com/DES-Lab/AALpy) | Python SUL interface; deterministic, nondeterministic and stochastic models | L*, KV and other algorithms; random W-method, random-word/walk testing; query cache and nondeterminism checks; RPNI passive learning | Hashable finite alphabet can encode concrete typed templates; this is not automatic infinite-domain inference | Examples, model serialization/visualization and runnable automata | Chosen baseline, not a competing novel method |
| [ALEX](https://github.com/LearnLib/alex/blob/main/README.md) | LearnLib-based learning/testing of web applications and JSON APIs | Active learning and automated tests, mapped abstract symbols | Configurable actions map abstract inputs to application interactions; detailed limits not audited | Existing web application/workbench | Major overlap: an interactive learning workbench is not new. Our local Python workflow is an integration choice |
| [RALib](https://github.com/LearnLib/ralib) | Register automata and data-dependent behavior | Specialized active learning and symbolic query infrastructure | Relations over data values, beyond a fixed representative alphabet | Research implementation and benchmarks; standalone twin export not established by this audit | Important prior art for M5; do not label finite templates register learning |
| BlackBox Twin current build | Owned local JSON-lines processes; deterministic finite Mealy hypothesis | AALpy L* + random W-method; physical budgets; SQLite events; model checkpoints | Explicit Action schema; fixed empty-argument order templates only | Local CLI, separate evaluation and dependency-free learned-model interpreter | Engineering integration; no measured advantage over AALpy |

## What was verified in the installed foundation

AALpy 2.0.0 `run_Lstar` accepts a SUL, an equivalence oracle, optional samples,
counterexample processing, caching/nondeterminism checking, and statistics return.
`SUL.pre`, `step`, and `post` supply the process adapter lifecycle. Installed
`RandomWMethodEqOracle` tests state access prefixes, randomized walks and characterization
suffixes. It returns counterexamples to L*, which can refine its observation table.
Finite randomized testing does not implement a true equivalence oracle.
The default AALpy cache is retained; our physical counter sits below it.
`run_RPNI` exists for the later passive baseline; it is not benchmarked in this milestone.
See [official examples](https://github.com/DES-Lab/AALpy/blob/master/Examples.py).

## Primary research and implications

- [Angluin, Learning Regular Sets from Queries and Counterexamples (1987)](https://homepages.math.uic.edu/~lreyzin/papers/angluin87.pdf): membership and equivalence queries underlie L*. A finite testing surrogate does not inherit the teacher's exact-equivalence guarantees. Our Mealy implementation is supplied by AALpy.
- [Dierl et al., Scalable Tree-based Register Automata Learning (TACAS 2024)](https://arxiv.org/abs/2401.14324): data relations and query efficiency already have specialized algorithms, implemented in RALib. Representative-value experiments are a narrower scope.
- [Frank et al., Learning Automata with Name Allocation (2025; revised March 2026)](https://arxiv.org/abs/2502.11947): explicit name binding and infinite alphabets require principled treatment. Dropping identifiers is not an adequate substitute.
- [Kruger, Junges and Rot, Error-awareness Accelerates Active Automata Learning (2026)](https://arxiv.org/abs/2602.21674): error-aware acceleration already uses domain assumptions. A future error-aware planner must compare against this prior art rather than claim error exploitation itself as new.
- [Official Z3 guide](https://microsoft.github.io/z3guide/): SMT solving can distinguish bounded candidate predicates. No such bottleneck is present in our finite-alphabet baseline; Z3 is deferred.

## Contribution classification and decision gate

1. **Established reuse:** Mealy models, L*, membership queries, randomized W-method testing, caching and counterexample processing.
2. **New repository integration:** recorded local process interactions, physical budgets, frozen-model evaluation and standalone learned-model export. These are not claims of first invention.
3. **Engineering improvement candidates:** auditable cost accounting and portable experiment artifacts. Usability and reliability must be measured before comparative claims.
4. **Experimental hypotheses:** a cost-aware planner or typed partition refinement might improve fidelity per physical action. Neither has been implemented or demonstrated.
5. **Original contributions:** none established. A future proposal requires focused literature review and controlled comparison against standard AALpy, LearnLib/ALEX and relevant data-learning work.

Unresolved: comparative query efficiency, whether our eventual typed workflow adds value over
RALib/ALEX mappings, and whether twin export offers benefits beyond existing model interpreters.
No capability is declared absent from another tool without a dedicated verification.

## M3 method attribution

Deletion minimization follows the established delta-debugging approach of
[Zeller and Hildebrandt, Simplifying and Isolating Failure-Inducing Input (2002)](https://doi.org/10.1109/32.988498),
with fresh process resets and a single-deletion fixed-point check. Its guarantee is local
to the tested reduction procedure, not a globally shortest input. The state-cover extension
planner is a bounded established model-based testing policy; it is not presented as a full
W-method implementation or a new query-selection method. Automatic refinement uses the
installed [AALpy L* observation-sample and equivalence-oracle interfaces](https://github.com/DES-Lab/AALpy/blob/master/aalpy/learning_algs/deterministic/LStar.py).
M3 demonstrates engineering integration and faithful use of those methods, not a new
learning algorithm.
