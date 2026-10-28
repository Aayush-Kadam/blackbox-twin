"""Owned delayed-observation fixture. Learner only receives its JSON protocol."""

import json
import sys

progress = 0
for line in sys.stdin:
    request = json.loads(line)
    if request == {"control": "reset"}:
        progress = 0
        response = {"control": "reset", "ok": True}
    elif request.get("arguments"):
        response = {"error": "unsupported_arguments"}
    elif request.get("operation") == "advance":
        progress = min(progress + 1, 4)
        response = {"ok": True}
    elif request.get("operation") == "commit":
        response = {"result": "accepted" if progress == 4 else "denied"}
        progress = 0
    elif request.get("operation") == "idle":
        response = {"ok": True}
    else:
        response = {"error": "unknown_operation"}
    print(json.dumps(response), flush=True)
