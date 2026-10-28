"""Dependency-free, deliberately restricted typed/guard interpreter; embedded in twins."""


def validation_error(action, contract):
    operation, arguments = action.get("operation"), action.get("arguments")
    if operation not in contract["operations"]:
        return "unknown_operation"
    schema = contract["operations"][operation]
    if not isinstance(arguments, dict) or set(arguments) - set(schema):
        return "invalid_arguments"
    for name, spec in schema.items():
        if name not in arguments:
            if spec.get("optional", False):
                continue
            return "invalid_arguments"
        value = arguments[name]
        if value is None and spec.get("nullable", False):
            continue
        kind = spec["kind"]
        if kind == "integer":
            if type(value) is not int:
                return "invalid_arguments"
            if not spec["minimum"] <= value <= spec["maximum"]:
                return "out_of_domain"
        elif kind == "boolean":
            if type(value) is not bool:
                return "invalid_arguments"
        elif kind == "enum":
            if not any(type(value) is type(v) and value == v for v in spec["values"]):
                return "invalid_arguments"
        else:
            return "unsupported_schema"
    return None


def predicate_matches(predicate, balance, amount):
    value = amount + predicate["coefficient"] * balance
    if predicate["operator"] == "le":
        return value <= predicate["constant"]
    if predicate["operator"] == "ge":
        return value >= predicate["constant"]
    raise ValueError("Unsupported predicate")


def updated_balance(update, balance, amount):
    kind = update["kind"]
    if kind == "keep":
        return balance
    if kind == "add":
        return balance + amount
    if kind == "subtract":
        return balance - amount
    if kind == "constant":
        return update["value"]
    raise ValueError("Unsupported update")


def guarded_step(model, state, action):
    if state is None:
        return None, {"bbt_unsupported": True, "reason": "unknown_state_until_reset"}
    balance, frozen = state
    error = validation_error(action, model["contract"])
    if error:
        if error == "unsupported_schema":
            return state, {"bbt_unsupported": True, "reason": error}
        return state, {"status": "error", "error": error, "balance": balance, "frozen": frozen}
    amount = action["arguments"].get("amount", 0)
    matches = [
        r
        for r in model["rules"]
        if r["operation"] == action["operation"]
        and r["frozen_context"] is frozen
        and all(predicate_matches(p, balance, amount) for p in r["guard"])
    ]
    if len(matches) != 1:
        return None, {"bbt_unsupported": True, "reason": "ambiguous_or_uncovered_guard"}
    rule = matches[0]
    values = {updated_balance(u, balance, amount) for u in rule["updates"]}
    if len(values) != 1:
        return None, {"bbt_unsupported": True, "reason": "ambiguous_update"}
    following = values.pop(), rule["output"]["frozen"]
    if list(following) not in model["states"]:
        return None, {"bbt_unsupported": True, "reason": "unobserved_state"}
    output = {**rule["output"], "balance": following[0]}
    return following, output
