# M6 model-class support matrix

Support here means representability/interface support, not successful reconstruction
at every tested budget. Measured accuracy is reported separately.

| Feature | Finite fixed/concrete model | Wallet guarded models 2/3 | M6 evaluation |
|---|---|---|---|
| Deterministic finite control | Supported on declared finite alphabet | Observable-state hypothesis only | Random, delayed, rare, wallet and inventory |
| Bounded integer input | Concrete templates only | Supported in declared -8..8 domain | Wallet and inventory quantity inputs |
| State-dependent inequalities | Encoded as finite states/templates | Restricted three-term grammar | Wallet caps/minimums/frozen variants |
| Equality | Concrete matching | Partial: conjunctions within term limit | Adversarial unit cases, not arbitrary equality synthesis |
| Arithmetic keep/add/subtract | Outputs memorized per state/template | Supported restricted updates | Wallet subtract/keep variants |
| Two independent counters | Partial: finite expansion over selected inputs | Unsupported | Inventory compatibility rejection and concrete baseline |
| Boolean/enum/optional schemas | Can enumerate chosen templates | Validation infrastructure, inference not established | Not evaluated as new target parameters |
| Symbolic references/generated IDs | Unsupported general binding | Unsupported | Not evaluated as successful features |
| Nondeterminism/time dependence | Outside assumptions | Outside assumptions | Not supported |
| Unbounded state/domain | Unsupported | Unsupported | Not evaluated |

Inventory output counters are not renamed into wallet balance/frozen fields. Its guarded
arms explicitly report model-class unsupported with zero training calls; this is not an
efficiency success. The concrete baseline uses only learned Mealy transitions. It refuses
unknown argument values, invalidates state after an unknown-effect input, and resets only
through the trusted protocol. No inventory business rules are copied into the twin.
