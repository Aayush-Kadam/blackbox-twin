# M5.0 frozen wallet contract — bbt-typed-wallet-v1

The machine-readable public contract is `examples/typed_wallet/contract.json`.
Amounts are exact integers -8..8; observable balances are integers 0..4. Operations are
`deposit(amount)`, `withdraw(amount)`, `get_balance()`, `freeze()`, `unfreeze()`.
These preserve the readiness document's deposit/withdraw names; no credit/debit aliases.
Sequences are at most 40 actions. Reset sets balance=0, frozen=false and acknowledges
the exact existing JSON reset protocol. Every valid JSON action returns status, balance,
frozen, and an error string when status=error. No money or external service is involved.

The action envelope remains the existing `{operation, arguments}` representation.
Amount is required for deposit/withdraw. Missing, null, Boolean, floating point and string
amounts, extra argument fields, and arguments to zero-argument operations yield
`invalid_arguments`. Integers outside -8..8 yield `out_of_domain`; an unknown operation
yields `unknown_operation`. Public validation errors preserve state. Reset is a distinct
control message. Malformed JSON/transport errors remain infrastructure failures and are
not used to infer wallet rules. The typed infrastructure separately supports strict
Boolean, enum and optional fields with explicit nullability; these are not wallet inputs.

Behavioral acceptance, rejection precedence, transaction limits, maximum attainable
balance, freezing behavior and updates are hidden from the learner. Public balance
bounds do not reveal the attainable cap or transaction limit. All numerical state is
observable in outputs; treating these fields as sufficient state is a falsifiable model
assumption, checked for inconsistent transitions and varied access contexts. This is a
bounded synthetic problem, not arbitrary software or general register learning.

Before inference implementation: freeze this file, manifest and owned fixture source
hashes in `evidence/m5-contract-freeze.json`. Development uses one configuration and
evaluation uses two separate configurations under the same protocol. Learners receive
only the public contract and a process oracle, never variant configuration or source.
The launcher fingerprints fixture source/config for provenance; fingerprints are not
learning features. Evaluation rules remain frozen. Any later semantic change requires a
new contract identifier and a new evidence directory.

Fixed training grid: -8,-1,0,1,8. Values -7,-5,-3,2,6,7 are reserved across all training,
including adaptive probes, counterexample searches and shrinking. Frozen evaluation
sequences are created before training; their outputs are acquired only after final
training and cannot refine the model. Exhaustive state/value evaluator checks are also
post-training and charged separately. Per method/variant ceiling: 5,000 training actions,
1,000 resets, 120 s, including initial membership, probing, differential search, shrinking,
refinement and regression replay. There is no binary-search monotonicity assumption.
