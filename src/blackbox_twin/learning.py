"""AALpy L* baseline, with physical budgeting and hypothesis checkpoints."""

import json
import random
from pathlib import Path

from aalpy.base import SUL
from aalpy.learning_algs import run_Lstar
from aalpy.oracles import RandomWMethodEqOracle

from .contracts import BehavioralModel, Observation, Transition


class LearningStalled(RuntimeError):
    pass


class RecordedSUL(SUL):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def pre(self):
        self.session.pre()

    def post(self):
        self.session.post()

    def step(self, letter):
        return json.dumps(self.session.step(letter).payload, sort_keys=True, separators=(",", ":"))


def serialize(hypothesis, actions, provenance):
    names = {s: f"S{i}" for i, s in enumerate(hypothesis.states)}
    return BehavioralModel(
        initial_state=names[hypothesis.initial_state],
        actions=actions,
        transitions={
            names[s]: {
                a: Transition(
                    next_state=names[s.transitions[a]],
                    output=Observation(payload=json.loads(s.output_fun[a])),
                )
                for a in actions
            }
            for s in hypothesis.states
        },
        provenance=provenance,
    )


def learn(
    session,
    model_path: Path,
    seed=7,
    walks=25,
    walk_length=8,
    samples=None,
    confirmed=None,
    provenance=None,
    preserve_checkpoints=False,
    equivalence_factory=None,
    checkpoint_hook=None,
    sul_factory=RecordedSUL,
):
    random.seed(seed)
    sul = sul_factory(session)
    alphabet = list(session.target.actions)
    checkpoint_count = 0
    confirmed = confirmed or []
    returned_counterexamples = []
    returned_signatures = set()
    delegate = equivalence_factory(alphabet, sul) if equivalence_factory else None

    class CheckpointOracle(RandomWMethodEqOracle):
        def find_cex(self, hypothesis):
            nonlocal checkpoint_count
            session.check("clock")
            checkpoint_count += 1
            if checkpoint_count > 100:
                raise LearningStalled("hypothesis_limit_reached")
            snapshot = serialize(
                hypothesis,
                session.target.actions,
                {
                    **(provenance or {}),
                    "algorithm": "AALpy L*",
                    "eq_oracle": (
                        getattr(delegate, "method", type(delegate).__name__)
                        if delegate is not None
                        else "RandomWMethodEqOracle"
                    ),
                    "seed": seed,
                    "revision": checkpoint_count,
                    "equivalence_proven": False,
                },
            )
            model_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
            if preserve_checkpoints:
                checkpoint = model_path.with_name(f"hypothesis-{checkpoint_count:03}.json")
                with checkpoint.open("x", encoding="utf-8") as out:
                    out.write(snapshot.model_dump_json(indent=2))
            session.recorder.artifact("hypothesis", snapshot.model_dump())
            if checkpoint_hook:
                checkpoint_hook(snapshot)
            for word, outputs in confirmed:
                hypothesis.reset_to_initial()
                predicted = [hypothesis.step(symbol) for symbol in word]
                if predicted != outputs:
                    divergence = next(
                        i for i, (a, b) in enumerate(zip(predicted, outputs, strict=True)) if a != b
                    )
                    # AALpy Mealy RS processing needs a differing FINAL output.
                    prefix = tuple(word[: divergence + 1])
                    signature = (
                        json.dumps(snapshot.model_dump(exclude={"provenance"}), sort_keys=True),
                        prefix,
                    )
                    if signature in returned_signatures:
                        raise LearningStalled("repeated_hypothesis_and_counterexample")
                    returned_signatures.add(signature)
                    returned_counterexamples.append(list(prefix))
                    session.recorder.artifact(
                        "confirmed_counterexample_returned",
                        {
                            "actions": list(prefix),
                            "full_observation_actions": list(word),
                            "expected": list(outputs[: divergence + 1]),
                            "hypothesis_outputs": predicted[: divergence + 1],
                            "hypothesis": checkpoint_count,
                        },
                    )
                    return prefix
            if delegate is not None:
                delegate.sul = self.sul
                result = delegate.find_cex(hypothesis)
                self.num_queries, self.num_steps = delegate.num_queries, delegate.num_steps
                return result
            return super().find_cex(hypothesis)

    eq = CheckpointOracle(alphabet, sul, walks_per_state=walks, walk_len=walk_length)
    if equivalence_factory is not None:
        session.learning_oracle = eq
    _, stats = run_Lstar(
        alphabet, sul, eq, "mealy", samples=samples, return_data=True, print_level=0
    )
    if confirmed:
        stats["confirmed_counterexamples_returned"] = returned_counterexamples
    session.post()
    return BehavioralModel.model_validate_json(model_path.read_text()), stats
