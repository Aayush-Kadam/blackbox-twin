# Generated from a learned finite model. No oracle or package dependency.
import json
import sys

MODEL = json.loads('{"schema_version":1,"initial_state":"S0","actions":{"advance":{"operation":"advance","arguments":{}},"commit":{"operation":"commit","arguments":{}},"idle":{"operation":"idle","arguments":{}}},"transitions":{"S0":{"advance":{"next_state":"S0","output":{"payload":{"ok":true}}},"commit":{"next_state":"S0","output":{"payload":{"result":"denied"}}},"idle":{"next_state":"S0","output":{"payload":{"ok":true}}}}},"provenance":{"run_id":"b1d440a7-68a6-4a2b-a95c-f7a7fa926428","algorithm":"AALpy L*","eq_oracle":"RandomWMethodEqOracle","seed":7,"revision":1,"equivalence_proven":false},"unsupported":"All concrete actions outside the enumerated alphabet"}')
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
