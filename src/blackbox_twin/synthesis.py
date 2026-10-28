"""Generate a dependency-free transition interpreter from a learned model."""

from pathlib import Path

from .contracts import BehavioralModel


def generate_twin(model: BehavioralModel, destination: Path):
    if model.schema_version == 3:
        runtime = Path(__file__).with_name("typed_runtime.py").read_text(encoding="utf-8")
        policy = Path(__file__).with_name("support_runtime.py").read_text(encoding="utf-8")
        policy = policy.replace("from .typed_runtime import validation_error\n", "")
        source = "import json\nimport sys\n" + runtime + "\n" + policy
        source += "\nMODEL = json.loads(" + repr(model.model_dump_json()) + ")\n"
        source += """
state = (0, False)
explain = "--explain" in sys.argv
for line in sys.stdin:
    try:
        request = json.loads(line)
        if request == {"control": "reset"}:
            state, output = (0, False), {"control": "reset", "ok": True}
            support = {"status": "OBSERVED", "reason": "trusted_reset_contract"}
        else:
            state, output, support = supported_step(MODEL, state, request)
    except (ValueError, TypeError, KeyError, AttributeError):
        state = None
        support = {"status": "UNSUPPORTED", "reason": "malformed_request"}
        output = {"bbt_unsupported": True, "support_status": "UNSUPPORTED",
                  "reason": "malformed_request"}
    print(json.dumps({"output": output, "support": support} if explain else output), flush=True)
"""
        destination.write_text(source, encoding="utf-8")
        return
    if model.schema_version == 2:
        runtime = Path(__file__).with_name("typed_runtime.py").read_text(encoding="utf-8")
        source = "import json\nimport sys\n" + runtime
        source += "\nMODEL = json.loads(" + repr(model.model_dump_json()) + ")\n"
        source += """
state = (0, False)
for line in sys.stdin:
    try:
        request = json.loads(line)
        if request == {"control": "reset"}:
            state, output = (0, False), {"control": "reset", "ok": True}
        else:
            state, output = guarded_step(MODEL, state, request)
    except (ValueError, TypeError, KeyError, AttributeError):
        state, output = None, {"bbt_unsupported": True, "reason": "malformed_request"}
    print(json.dumps(output), flush=True)
"""
        destination.write_text(source, encoding="utf-8")
        return
    encoded = repr(model.model_dump_json())
    source = """# Generated from a learned finite model. No oracle or package dependency.
import json
import sys

MODEL = json.loads(MODEL_JSON)
state = MODEL["initial_state"]
for line in sys.stdin:
    try:
        request = json.loads(line)
        if request == {"control": "reset"}:
            state = MODEL["initial_state"]
            output = {"control": "reset", "ok": True}
        else:
            symbol = next((key for key, action in MODEL["actions"].items()
                           if action == request), None)
            if symbol is None:
                output = {"bbt_unsupported": True, "reason": "outside_learned_alphabet"}
            else:
                transition = MODEL["transitions"][state][symbol]
                output = transition["output"]["payload"]
                state = transition["next_state"]
    except (ValueError, TypeError, KeyError):
        output = {"bbt_unsupported": True, "reason": "malformed_request"}
    print(json.dumps(output), flush=True)
"""
    destination.write_text(source.replace("MODEL_JSON", encoded), encoding="utf-8")
