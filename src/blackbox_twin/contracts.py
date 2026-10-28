"""Versioned, strict interchange contracts. JSON output comparison is exact."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Action(Contract):
    operation: str = Field(min_length=1)
    arguments: dict[str, JsonValue] = Field(default_factory=dict)


class Observation(Contract):
    # Target errors are ordinary outputs, never transport errors.
    payload: dict[str, JsonValue]


class Target(Contract):
    schema_version: Literal[1] = 1
    target_id: str
    version: str
    executable: str
    authorization: Literal["owned-local-fixture"]
    reset: Literal["protocol"] = "protocol"
    actions: dict[str, Action]


class QueryBudget(Contract):
    max_actions: int = Field(default=10000, ge=0)
    max_resets: int = Field(default=3000, ge=0)
    max_sequence_length: int = Field(default=100, ge=1)
    query_timeout_seconds: float = Field(default=2.0, gt=0)
    total_seconds: float = Field(default=120.0, gt=0)


class Costs(Contract):
    actions: int = 0
    resets: int = 0
    sequences: int = 0
    oracle_seconds: float = 0.0


class Experiment(Contract):
    schema_version: Literal[1] = 1
    experiment_id: str
    phase: str
    started_at: str
    actions: list[str]
    observations: list[Observation]
    status: str


class Transition(Contract):
    next_state: str
    output: Observation


class BehavioralModel(Contract):
    schema_version: Literal[1] = 1
    initial_state: str
    actions: dict[str, Action]
    transitions: dict[str, dict[str, Transition]]
    provenance: dict[str, JsonValue] = Field(default_factory=dict)
    unsupported: str = "All concrete actions outside the enumerated alphabet"

    @model_validator(mode="after")
    def total_machine(self):
        if self.initial_state not in self.transitions:
            raise ValueError("Unknown initial state")
        for row in self.transitions.values():
            if set(row) != set(self.actions):
                raise ValueError("Transition row does not match alphabet")
            if any(t.next_state not in self.transitions for t in row.values()):
                raise ValueError("Unknown successor state")
        return self

    def predict(self, word: list[str] | tuple[str, ...]) -> list[Observation]:
        state = self.initial_state
        outputs = []
        for symbol in word:
            if symbol not in self.actions:
                raise ValueError(f"Unsupported model symbol: {symbol}")
            transition = self.transitions[state][symbol]
            outputs.append(transition.output)
            state = transition.next_state
        return outputs


class Counterexample(Contract):
    schema_version: Literal[1] = 1
    actions: list[str]
    expected: list[Observation]
    predicted: list[Observation]
    first_divergence: int
    model_sha256: str


class Oracle(Protocol):
    def reset(self) -> None: ...
    def step(self, action: Action) -> Observation: ...
