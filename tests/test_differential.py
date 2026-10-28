import pytest

from blackbox_twin.contracts import Action, Costs, Observation, QueryBudget, Target
from blackbox_twin.counterexamples import Corpus, UnsupportedDependency, minimize
from blackbox_twin.differential import DifferentialRunner, compare_traces
from blackbox_twin.experiments import guided_sequences, random_sequences
from blackbox_twin.oracle import ProcessOracle, Session
from blackbox_twin.storage import Recorder


def observations(payloads):
    return [Observation(payload=payload) for payload in payloads]


@pytest.mark.parametrize(
    "left,right,status,path",
    [
        ([{"x": 1}], [{"x": 1}], "agreement", []),
        ([{"x": 1}], [{"x": 2}], "output_disagreement", ["/x"]),
        ([{"error": "a"}], [{"error": "b"}], "error_code_disagreement", ["/error"]),
        ([{"x": 1}], [{"y": 1}], "structural_disagreement", ["/x", "/y"]),
        ([{"x": [1]}], [{"x": []}], "structural_disagreement", ["/x"]),
        ([{"x": True}], [{"x": 1}], "structural_disagreement", ["/x"]),
        ([{"a/b": {"~": 1}}], [{"a/b": {"~": 2}}], "output_disagreement", ["/a~1b/~0"]),
        ([{"x": 1}], [], "sequence_length_disagreement", [""]),
        ([{"x": 1}], [{"bbt_unsupported": True}], "unsupported_twin", []),
        ([{"bbt_unsupported": True}], [{"bbt_unsupported": True}], "agreement", []),
    ],
)
def test_exact_comparison(left, right, status, path):
    result = compare_traces(["a"], observations(left), observations(right))
    assert result.status == status
    assert result.divergent_paths == path
    assert result.raw_original == left
    assert result.raw_twin == right
    assert not result.is_mismatch if status == "unsupported_twin" else True


@pytest.mark.parametrize(
    "side,behavior,status",
    [
        ("original", "raise SystemExit(0)", "crash"),
        ("twin", "raise SystemExit(0)", "crash"),
        ("original", "import time; time.sleep(2)", "timeout"),
        ("twin", "import sys\nfor line in sys.stdin: print('{}', flush=True)", "reset_failure"),
        (
            "original",
            "import sys\nfor line in sys.stdin: print('bad', flush=True)",
            "reset_failure",
        ),
    ],
)
def test_real_process_failure_classification(tmp_path, side, behavior, status):
    healthy = """import sys,json
for line in sys.stdin:
 request=json.loads(line)
 response={"control":"reset","ok":True} if "control" in request else {"ok":True}
 print(json.dumps(response),flush=True)
"""
    target = Target(
        target_id="fault-injection",
        version="1",
        executable="unused",
        authorization="owned-local-fixture",
        actions={"a": Action(operation="a")},
    )
    recorder = Recorder(tmp_path / "fault.sqlite", {"fault_injection": True})
    sessions = []
    for label in ("original", "twin"):
        path = tmp_path / f"{label}.py"
        path.write_text(behavior if label == side else healthy)
        sessions.append(
            Session(
                ProcessOracle(path),
                target,
                QueryBudget(query_timeout_seconds=0.2 if status == "timeout" else 2.0),
                recorder,
                label,
            )
        )
    try:
        result = DifferentialRunner(*sessions).run(["a"])
        assert result.status == status, result
        assert result.failure_side == side
        assert not result.is_mismatch
    finally:
        for session in sessions:
            session.oracle.close()
        recorder.close("test_completed")


class FaultInjectedRunner:
    """Unit-only fault injection. This does not constitute genuine learning refinement."""

    def __init__(self, predicate):
        from types import SimpleNamespace

        self.original = SimpleNamespace(
            target=Target(
                target_id="injected",
                version="1",
                executable="unused",
                authorization="owned-local-fixture",
                actions={s: Action(operation=s) for s in ("a", "b", "x")},
            ),
            costs=Costs(),
        )
        self.predicate = predicate
        self.calls = []

    def run(self, word):
        self.calls.append(list(word))
        self.original.costs.actions += len(word)
        left = [{"value": 0} for _ in word]
        right = [dict(p) for p in left]
        if word and self.predicate(word):
            right[-1] = {"value": 1}
        return compare_traces(word, observations(left), observations(right))


@pytest.mark.parametrize(
    "word,predicate,expected",
    [
        (["a"], lambda w: "a" in w, ["a"]),
        (["x", "a", "b", "x"], lambda w: "a" in w and "b" in w, ["a", "b"]),
        (["a", "b"], lambda w: list(w) == ["a", "b"], ["a", "b"]),
    ],
)
def test_deletion_minimization(word, predicate, expected):
    runner = FaultInjectedRunner(predicate)
    initial = runner.run(word)
    result = minimize(runner, initial)
    assert result.status == "completed"
    assert result.locally_minimal
    assert result.minimized.actions == expected
    assert result.minimized.is_mismatch
    assert runner.run(expected).is_mismatch
    assert runner.calls[1] == word  # Reproduction before any deletion.


def test_minimization_non_reproduction_and_budget():
    runner = FaultInjectedRunner(lambda w: True)
    initial = runner.run(["a", "b"])
    assert minimize(runner, initial, max_actions=0).status == "budget_exhausted"
    result = minimize(runner, initial, max_actions=2)
    assert result.minimized.is_mismatch
    assert not result.locally_minimal
    assert result.physical_actions <= 2
    runner.predicate = lambda w: False
    assert minimize(runner, initial).status == "non_reproducing"


def test_minimization_stops_on_timeout():
    from blackbox_twin.differential import Comparison

    runner = FaultInjectedRunner(lambda w: "a" in w)
    initial = runner.run(["x", "a", "x"])
    original_run = runner.run
    calls = 0

    def interrupted(word):
        nonlocal calls
        calls += 1
        if calls > 1:
            return Comparison(actions=list(word), status="timeout", failure_side="original")
        return original_run(word)

    runner.run = interrupted
    result = minimize(runner, initial)
    assert result.status == "timeout"
    assert result.minimized.is_mismatch
    assert not result.locally_minimal


def test_level_one_real_faulty_twin(tmp_path):
    from blackbox_twin.contracts import BehavioralModel, Transition
    from blackbox_twin.synthesis import generate_twin

    target = Target(
        target_id="controlled-fault",
        version="1",
        executable="unused",
        authorization="owned-local-fixture",
        actions={s: Action(operation=s) for s in ("a", "b", "x")},
    )
    script = tmp_path / "constant-target.py"
    script.write_text("""import sys,json
for line in sys.stdin:
 request=json.loads(line)
 output={"control":"reset","ok":True} if "control" in request else {"value":0}
 print(json.dumps(output),flush=True)
""")
    # Explicitly constructed faulty table for machinery validation, not learning evidence.
    faulty = BehavioralModel(
        initial_state="S0",
        actions=target.actions,
        transitions={
            "S0": {
                s: Transition(next_state="S0", output=Observation(payload={"value": int(s == "b")}))
                for s in target.actions
            }
        },
    )
    twin_path = tmp_path / "faulty-twin.py"
    generate_twin(faulty, twin_path)
    recorder = Recorder(tmp_path / "fault.sqlite", {"fault_injection": True})
    original = Session(ProcessOracle(script), target, QueryBudget(), recorder, "original")
    twin = Session(ProcessOracle(twin_path), target, QueryBudget(), recorder, "twin")
    runner = DifferentialRunner(original, twin)
    try:
        result = minimize(runner, runner.run(["x", "a", "b", "x"]))
        assert result.status == "completed"
        assert result.minimized.actions == ["b"]
        assert runner.run(["b"]).is_mismatch
        assert original.costs.resets == twin.costs.resets
        assert original.costs.resets >= result.attempts + 2
    finally:
        original.oracle.close()
        twin.oracle.close()
        recorder.close("test_completed")


def test_symbolic_dependency_fails_closed():
    runner = FaultInjectedRunner(lambda w: True)
    initial = runner.run(["a"])
    runner.original.target.actions["a"] = Action(operation="a", arguments={"ref": "@missing"})
    before = len(runner.calls)
    with pytest.raises(UnsupportedDependency):
        minimize(runner, initial)
    assert len(runner.calls) == before


def test_corpus_persistence_and_append_only_outcomes(tmp_path, session):
    from blackbox_twin.learning import learn

    runner = FaultInjectedRunner(lambda w: "a" in w)
    minimized = minimize(runner, runner.run(["x", "a", "x"]))
    model, _ = learn(session, tmp_path / "model.json", walks=1, walk_length=1)
    corpus = Corpus(tmp_path / "corpus")
    record = corpus.add(runner.original.target, model, minimized, "fault-injection", 7, {})
    path = tmp_path / "corpus" / record.counterexample_id / "discovery.json"
    before = path.read_bytes()
    assert corpus.read(path) == record
    corpus.outcome(record, {"status": "resolved"})
    corpus.outcome(record, {"status": "replayed"})
    assert len(list(path.parent.glob("outcome-*.json"))) == 2
    assert path.read_bytes() == before


def test_seeded_strategies(session, tmp_path):
    from blackbox_twin.learning import learn

    assert list(random_sequences(["a", "b"], seed=11)) == list(
        random_sequences(["a", "b"], seed=11)
    )
    model, _ = learn(session, tmp_path / "model.json", walks=1, walk_length=1)
    candidates = list(guided_sequences(model, depth=2, count=40, max_length=5))
    assert len(candidates) == 40
    assert len(set(candidates)) == 40
    assert all(len(word) <= 5 for word in candidates)
