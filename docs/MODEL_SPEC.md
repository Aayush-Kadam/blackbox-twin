# Supported model and protocol, version 1

The initial class is deterministic, resettable local programs whose behavior under a declared
finite alphabet admits a finite Mealy abstraction. The invocation contract is supplied;
the transition rules are unknown to the learner. Reset and determinism are assumptions
checked by repeated probes, not proved by those probes.

An Action has `operation: str` and `arguments: dict[str, JSON]`. A Target maps unique
finite symbols to concrete Actions. A request is one JSON object per line. The response
must be a JSON object, at most 65,536 bytes including its newline. Requests are bounded
to 1,024 encoded bytes. Target-generated errors remain ordinary observable payloads.
Malformed JSON, EOF, failed reset acknowledgments and timeouts are infrastructure failures.

`{"control":"reset"}` must return exactly `{"control":"reset","ok":true}`.
Reset precedes each physical experiment. The initial fixture is one order lifecycle;
no amounts, generated IDs, multi-order behavior or partial payments are modeled.

For alphabet A, a target trace function T maps a finite word in A* to its sequence of
response objects after reset. The hypothesis M has states Q, initial q0 and total
transition/output functions over A. Two implementations agree on a set W exactly when
T(w) = M(w) for every w in W, comparing complete JSON payloads recursively. Object key
order is irrelevant; array order, amounts, codes and fields are retained. The declared
JSON data contract must not rely on numeric lexical formatting (e.g. `1` versus `1.0`).

No normalization is performed. Output JSON is encoded canonically only to make AALpy
symbols hashable; no fields are removed. Dynamic identifiers and symbolic references are
unsupported in this slice. A future binding layer must declare creation sites, typed
bindings, scope and replay semantics before using them.

- Exact concrete output agreement: equal parsed payloads for a particular experiment.
- Abstract-symbol agreement: equality after a separately declared abstraction; not used here.
- Bounded agreement: every word in an explicitly enumerated finite set agrees.
- Sampled agreement: only the sampled set is checked (our CLI evaluation).
- Proven equivalence: requires a valid proof and assumptions; never claimed by this build.

The serialized BehavioralModel contains `schema_version`, finite actions, initial state,
total transition rows, outputs, provenance and unsupported-region description. Successor
states and rows are validated on load. State IDs S0, S1, ... are neutral learned IDs.
A standalone twin interprets this table, not a list of complete training traces.
Unknown concrete inputs return `bbt_unsupported`, outside the target's error namespace,
without changing model state.

Canonical typed contracts also define Observation, Experiment, Oracle, QueryBudget,
Costs, Transition and Counterexample. The current database stores experiments and
individual events relationally; raw and normalized output are identical under version 1.

M3 adds `Comparison`, `Minimization` and `CorpusRecord` version-1 contracts. Comparison
uses recursive JSON semantics: booleans differ from numbers, object-key and list-length
differences are structural, and JSON pointers escape `~` and `/`. Output/error-code/structure/
length disagreements are distinct from timeout, crash, reset failure, unsupported twin input,
budget exhaustion and infrastructure failure. A finite trace may disagree before its last
action; learning receives the prefix ending at that first mismatch.

"Raw" here means parsed JSON response payloads before the identity comparison policy,
not original stdout bytes, whitespace, numeric spellings or key order. Both raw and
normalized fields are retained explicitly and no meaningful field is discarded. No dynamic
normalization changes occur during refinement. A deletion-minimal result means no single
action deletion preserves its mismatch category and divergent fields under the executed
procedure, with fresh resets. It does not mean globally shortest or argument-minimal.
