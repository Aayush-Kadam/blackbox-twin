"""Typed contracts over existing Action, Session, cache and evidence representations."""

import json
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Action, Contract
from .typed_runtime import validation_error


class ArgumentSchema(Contract):
    kind: Literal["integer", "boolean", "enum"]
    minimum: int | None = None
    maximum: int | None = None
    values: list[str | int | bool] = Field(default_factory=list)
    optional: bool = False
    nullable: bool = False

    @model_validator(mode="after")
    def valid_schema(self):
        if self.kind == "integer" and (
            self.minimum is None or self.maximum is None or self.minimum > self.maximum
        ):
            raise ValueError("Integer schemas require ordered finite bounds")
        if self.kind == "enum" and not self.values:
            raise ValueError("Enum schema requires values")
        return self


def validate_contract(contract):
    if contract.get("schema_version") != 1:
        raise ValueError("Unsupported typed contract version")
    for schema in contract["operations"].values():
        for spec in schema.values():
            ArgumentSchema.model_validate(spec)
    return contract


def action_key(action: Action, contract_id="bbt-typed-wallet-v1"):
    return (
        contract_id + ":" + json.dumps(action.model_dump(), sort_keys=True, separators=(",", ":"))
    )


def intern(target, action, contract_id="bbt-typed-wallet-v1"):
    key = action_key(action, contract_id)
    if key in target.actions and target.actions[key] != action:
        raise ValueError("Canonical action collision")
    target.actions[key] = action
    return key


def word_keys(target, actions, contract_id="bbt-typed-wallet-v1"):
    return [intern(target, a, contract_id) for a in actions]


def decode_word(target, word):
    return [target.actions[s] for s in word]


def validate_action(action, contract):
    return validation_error(action.model_dump(), validate_contract(contract))
