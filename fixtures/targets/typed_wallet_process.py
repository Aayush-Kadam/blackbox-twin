"""Owned evaluator fixture. Learners must not import or read this source."""

import json
import sys

CAP = 4
LIMIT = 3
balance, frozen = 0, False
for line in sys.stdin:
    request = json.loads(line)
    if request == {"control": "reset"}:
        balance, frozen = 0, False
        output = {"control": "reset", "ok": True}
    else:
        operation, arguments = request.get("operation"), request.get("arguments")
        error = None
        if operation not in {"deposit", "withdraw", "get_balance", "freeze", "unfreeze"}:
            error = "unknown_operation"
        elif not isinstance(arguments, dict):
            error = "invalid_arguments"
        elif operation in {"deposit", "withdraw"}:
            if set(arguments) != {"amount"} or type(arguments["amount"]) is not int:
                error = "invalid_arguments"
            elif not -8 <= arguments["amount"] <= 8:
                error = "out_of_domain"
            elif arguments["amount"] <= 0:
                error = "invalid_amount"
            elif frozen:
                error = "frozen"
            elif arguments["amount"] > LIMIT:
                error = "transaction_limit"
            elif operation == "deposit" and balance + arguments["amount"] > CAP:
                error = "capacity"
            elif operation == "withdraw" and arguments["amount"] > balance:
                error = "insufficient"
            elif operation == "deposit":
                balance += arguments["amount"]
            else:
                balance -= arguments["amount"]
        elif arguments:
            error = "invalid_arguments"
        elif operation == "freeze":
            frozen = True
        elif operation == "unfreeze":
            frozen = False
        output = {"status": "error" if error else "ok", "balance": balance, "frozen": frozen}
        if error:
            output["error"] = error
    print(json.dumps(output), flush=True)
