"""Owned synthetic oracle. This module is NEVER imported by the learner."""

import json
import sys


def main():
    state = "absent"
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request == {"control": "reset"}:
                state = "absent"
                output = {"control": "reset", "ok": True}
            else:
                op, args = request.get("operation"), request.get("arguments", {})
                output = None
                if op not in {"create", "authorize", "capture", "refund", "cancel", "status"}:
                    output = {"error": "unknown_operation"}
                elif args:
                    output = {"error": "unsupported_arguments"}
                elif op == "status":
                    output = {"status": state}
                elif op == "create":
                    if state == "absent":
                        state = "created"
                    else:
                        output = {"error": "already_exists"}
                elif state == "absent":
                    output = {"error": "no_order"}
                elif op == "authorize":
                    if state == "created":
                        state = "authorized"
                    else:
                        output = {"error": "authorization_not_allowed"}
                elif op == "capture":
                    if state == "authorized":
                        state = "captured"
                    else:
                        output = {"error": "capture_not_allowed"}
                elif op == "refund":
                    if state == "captured":
                        state = "refunded"
                    else:
                        output = {"error": "refund_not_allowed"}
                elif op == "cancel":
                    if state in {"created", "authorized"}:
                        state = "cancelled"
                    else:
                        output = {"error": "cancel_not_allowed"}
                if output is None:
                    output = {"ok": True, "status": state}
        except (ValueError, AttributeError):
            output = {"error": "malformed_request"}
        print(json.dumps(output), flush=True)


if __name__ == "__main__":
    main()
