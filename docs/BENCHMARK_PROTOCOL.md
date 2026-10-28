# Initial evaluation protocol (M0–M2)

Primary initial metric: exact held-out complete-trace match rate under the declared finite
alphabet. Secondary metrics: step match, target error-response match, state count, actions,
resets, library inference/search time and oracle interaction time. These are smoke results,
not the M6 comparative benchmark.

Reference configuration: AALpy 2.0.0 L*, default caching/nondeterminism check and RS
counterexample processing; RandomWMethodEqOracle, 25 walks per learned state and maximum
random walk length 8; seed 7; 10,000 physical actions, 3,000 resets, sequence limit 100,
2 seconds per call and 120 seconds total. Two alphabet-length reset probes consume
training-side budget and are included in reported physical costs.

After training completes, a separate CLI invocation loads the frozen model. Seed 2027
selects 100 distinct full words of length 9–20 uniformly by length, then independently
uniform symbols. Full words present in the training/reset-check experiment DB are rejected.
Prefixes and individual transitions may overlap training: this tests compositional
generalization, not unseen operations. Evaluation has a separate DB and budget, and no
evaluation outputs enter learning. Duplicate samples are rejected. Sampling effort is capped.
The distribution is conditioned on those exclusions; do not generalize to arbitrary traffic.

The two-state fixture is checked separately against evaluator-only ground truth on all 62
nonempty words through length 5. This is bounded exhaustive testing, not an equivalence
proof. The order fixture is also checked over 81 four-action words in a three-symbol
subalphabet, plus longer sampled sequences in tests.

Future M6 protocol must be frozen before final evaluation: random FSMs, order, session,
job and adversarial families; 10 seeds where feasible; matched physical action budgets;
random, breadth-first, standard active and applicable passive baselines; paired comparisons,
uncertainty intervals, planner ablations, failures and overhead. No superiority claim may be
made from the single smoke configuration. AALpy's `cache_saved` is a logical query count,
not a physical action saving. It must not be added to or subtracted from physical costs.
