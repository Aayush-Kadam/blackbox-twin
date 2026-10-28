"""Tiny independent recovery fixture, evaluated exhaustively only in tests."""

import json
import sys

state = False
for line in sys.stdin:
    request = json.loads(line)
    if request == {"control": "reset"}:
        state = False
        output = {"control": "reset", "ok": True}
    else:
        if request["operation"] == "flip":
            state = not state
        output = {"lit": state}
    print(json.dumps(output), flush=True)
