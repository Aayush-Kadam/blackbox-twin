"""Standalone policy runtime. Helpers validation_error and json are embedded by synthesis."""

import json

from .typed_runtime import validation_error


def supported_step(model, state, action):
    base = {"model_id": model["model_id"], "model_version": 3}
    if state is None:
        metadata = {**base, "status": "UNSUPPORTED", "reason": "unknown_state_until_reset"}
        return (
            None,
            {
                "bbt_unsupported": True,
                "support_status": "UNSUPPORTED",
                "reason": metadata["reason"],
            },
            metadata,
        )
    b, f = state
    if [b, f] not in model["states"]:
        metadata = {**base, "status": "UNSUPPORTED", "reason": "unobserved_state_context"}
        return (
            None,
            {
                "bbt_unsupported": True,
                "support_status": "UNSUPPORTED",
                "reason": metadata["reason"],
            },
            metadata,
        )
    error = validation_error(action, model["contract"])
    if error:
        if error == "unsupported_schema":
            metadata = {**base, "status": "UNSUPPORTED", "reason": error}
            return (
                None,
                {"bbt_unsupported": True, "support_status": "UNSUPPORTED", "reason": error},
                metadata,
            )
        # These state-preserving errors are explicitly specified by the PUBLIC frozen contract.
        return (
            state,
            {"status": "error", "error": error, "balance": b, "frozen": f},
            {
                **base,
                "status": "INFERRED_SUPPORTED",
                "reason": "public_validation_contract",
                "rule_ids": [],
            },
        )
    key = json.dumps(
        [b, f, action["operation"], action["arguments"].get("amount", 0)], separators=(",", ":")
    )
    cell = model["cells"].get(key)
    if cell is None:
        cell = {
            "status": "UNSUPPORTED",
            "reason": "unobserved_state_or_schema_context",
            "rule_ids": [],
        }
    metadata = {k: v for k, v in cell.items() if k not in {"output", "candidate_outputs"}}
    metadata.update(base)
    if cell["status"] in {"OBSERVED", "INFERRED_SUPPORTED"}:
        output = cell["output"]
        following = output["balance"], output["frozen"]
        return following, dict(output), metadata
    output = {"bbt_unsupported": True, "support_status": cell["status"], "reason": cell["reason"]}
    return None, output, metadata
