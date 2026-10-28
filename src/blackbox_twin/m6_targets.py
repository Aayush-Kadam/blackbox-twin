"""Evaluator-owned M6 generators/specifications. Never called by an inference function."""

import ast
import json
import random
from collections import deque

from .benchmark_targets import RUNNER
from .contracts import Action, Target
from .typed_runtime import validation_error

INVENTORY = """import json,sys
CAP, LIMIT = CONFIG
stock=held=0
for line in sys.stdin:
 r=json.loads(line)
 if r=={"control":"reset"}:
  stock=held=0
  o={"control":"reset","ok":True}
 else:
  op,args=r.get("operation"),r.get("arguments")
  error=None
  if op not in {"stock","reserve","release","consume","inspect"}: error="unknown_operation"
  elif not isinstance(args,dict): error="invalid_arguments"
  elif op in {"stock","reserve"}:
   if set(args)!={"quantity"} or type(args["quantity"]) is not int: error="invalid_arguments"
   elif not -8<=args["quantity"]<=8: error="out_of_domain"
   elif args["quantity"]<=0: error="invalid_quantity"
   elif op=="stock" and stock+args["quantity"]>CAP: error="capacity"
   elif op=="reserve" and args["quantity"]>LIMIT: error="reservation_limit"
   elif op=="reserve" and args["quantity"]>stock-held: error="insufficient"
   elif op=="stock": stock+=args["quantity"]
   else: held+=args["quantity"]
  elif args: error="invalid_arguments"
  elif op in {"release","consume"} and held==0: error="invalid_sequence"
  elif op=="release": held=0
  elif op=="consume": stock-=held; held=0
  o={"status":"error" if error else "ok","available":stock-held,"reserved":held}
  if error: o["error"]=error
 print(json.dumps(o),flush=True)
"""


def inventory_contract():
    return {
        "schema_version": 1,
        "contract_id": "bbt-inventory-v1",
        "amount_domain": [-8, 8],
        "operations": {
            op: {"quantity": {"kind": "integer", "minimum": -8, "maximum": 8}}
            if op in {"stock", "reserve"}
            else {}
            for op in ("stock", "reserve", "release", "consume", "inspect")
        },
        "state_fields": ["available", "reserved"],
        "fixed_grid": [-8, -1, 0, 1, 8],
        "reserved_evaluation_values": [-7, -5, -3, 3, 6, 7],
    }


def wallet_step(state, action, config, contract):
    b, f = state
    op, args = action["operation"], action["arguments"]
    error = validation_error(action, contract)
    if not error and op in {"deposit", "withdraw"}:
        q = args["amount"]
        checks = [
            (q < config["minimum"], "invalid_amount"),
            (f and config["freeze_blocks"], "frozen"),
            (q > config["limit"], "transaction_limit"),
            (op == "deposit" and q > config["cap"] - b, "capacity"),
            (op == "withdraw" and q > b, "insufficient"),
        ]
        error = next((name for flag, name in checks if flag), None)
        if error is None:
            b = b + q if op == "deposit" else b if config["withdraw_keep"] else b - q
    elif not error and op in {"freeze", "unfreeze"}:
        f = op == "freeze"
    output = {"status": "error" if error else "ok", "balance": b, "frozen": f}
    if error:
        output["error"] = error
    return (b, f), output


def inventory_step(state, action, config, contract):
    available, reserved = state
    op, args = action["operation"], action["arguments"]
    error = validation_error(action, contract)
    if not error and op in {"stock", "reserve"}:
        q = args["quantity"]
        if q < 1:
            error = "invalid_quantity"
        elif op == "stock":
            if available + reserved + q > config["cap"]:
                error = "capacity"
            else:
                available += q
        elif q > config["limit"]:
            error = "reservation_limit"
        elif q > available:
            error = "insufficient"
        else:
            available, reserved = available - q, reserved + q
    elif not error and op in {"release", "consume"}:
        if reserved == 0:
            error = "invalid_sequence"
        else:
            available += reserved if op == "release" else 0
            reserved = 0
    output = {"status": "error" if error else "ok", "available": available, "reserved": reserved}
    if error:
        output["error"] = error
    return (available, reserved), output


def concrete_actions(contract):
    actions = []
    for op, schema in contract["operations"].items():
        for value in contract["fixed_grid"] if schema else [None]:
            args = {next(iter(schema)): value} if schema else {}
            actions.append(Action(operation=op, arguments=args))
    return actions


def render(project, spec, wallet_contract):
    family, index = spec["family"], spec["variant"]
    contract, table = None, None
    rng = random.Random(spec["target_seed"])
    if spec["track"] == "A":
        if family in {"easy", "medium"}:
            n, size, outputs = (
                (3 + index, 2 + index % 2, 2) if family == "easy" else (8 + index, 3 + index % 2, 4)
            )
            alphabet = list("abcd"[:size])
            table = [
                {
                    a: [
                        (s + 1) % n if a == "a" else s if index == 0 else rng.randrange(n),
                        {"symbol": str(rng.randrange(outputs))},
                    ]
                    for a in alphabet
                }
                for s in range(n)
            ]
        elif family == "delayed":
            n, alphabet = [5, 7, 9][index], ["advance", "commit", "idle"]
            table = [
                {
                    "advance": [min(s + 1, n), {"ok": True}],
                    "idle": [s, {"ok": True}],
                    "commit": [0, {"result": "accepted" if s == n else "denied"}],
                }
                for s in range(n + 1)
            ]
        else:
            pattern, alphabet = ["abacaba", "bcabacaba", "cabbacabcab"][index], list("abc")
            table = [
                {
                    a: [
                        s + 1 if s < len(pattern) and a == pattern[s] else 0,
                        {"hit": s == len(pattern) and a == "c"},
                    ]
                    for a in alphabet
                }
                for s in range(len(pattern) + 1)
            ]
        source = RUNNER.replace("DATA", repr(json.dumps(table)))
        if family == "rare" and index == 0:
            source = (project / "evidence/m4-1/target-rare-access/oracle.py").read_text()
            tree = ast.parse(source)
            node = next(
                n
                for n in tree.body
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "TABLE" for t in n.targets)
            )
            assert table == json.loads(ast.literal_eval(node.value.args[0]))
        actions = {a: Action(operation=a) for a in alphabet}
    else:
        config = spec["parameters"]
        if spec["track"] == "B":
            contract = json.loads(json.dumps(wallet_contract))
            source = (project / "fixtures/targets/typed_wallet_process.py").read_text()
            source = source.replace("CAP = 4", f"CAP = {config['cap']}").replace(
                "LIMIT = 3", f"LIMIT = {config['limit']}"
            )
            source = (
                "MINIMUM="
                + str(config["minimum"])
                + "\nFREEZE_BLOCKS="
                + repr(config["freeze_blocks"])
                + "\nWITHDRAW_KEEP="
                + repr(config["withdraw_keep"])
                + "\n"
                + source
            )
            source = source.replace('arguments["amount"] <= 0', 'arguments["amount"] < MINIMUM')
            source = source.replace("elif frozen:", "elif frozen and FREEZE_BLOCKS:")
            source = source.replace(
                'balance -= arguments["amount"]',
                'balance -= 0 if WITHDRAW_KEEP else arguments["amount"]',
            )
        else:
            contract = inventory_contract()
            source = INVENTORY.replace("CONFIG", repr((config["cap"], config["limit"])))
        actions = {a.model_dump_json(): a for a in concrete_actions(contract)}
    target = Target(
        target_id=spec["id"],
        version="1",
        executable="oracle.py",
        authorization="owned-local-fixture",
        actions=actions,
    )
    return source, target, contract, table


def evaluation_inputs(spec, target, contract, seed):
    rng, cases = random.Random(seed), []
    for category in ("short", "long"):
        for _ in range(20 if spec["track"] == "A" else 10):
            length = rng.randint(16, 24) if category == "short" else rng.randint(48, 64)
            if spec["track"] == "A":
                words = [
                    rng.choice(list(target.actions.values())).model_dump() for _ in range(length)
                ]
                cases.append({"category": category, "actions": words})
            else:
                for values, label in [
                    (contract["fixed_grid"], "seen"),
                    (contract["reserved_evaluation_values"], "unseen"),
                ]:
                    words = []
                    for _ in range(length):
                        op = rng.choice(list(contract["operations"]))
                        schema = contract["operations"][op]
                        words.append(
                            Action(
                                operation=op,
                                arguments={next(iter(schema)): rng.choice(values)}
                                if schema
                                else {},
                            ).model_dump()
                        )
                    # Guarantee at least one typed value in every value stratum.
                    op = "deposit" if spec["track"] == "B" else "stock"
                    name = "amount" if spec["track"] == "B" else "quantity"
                    words[0] = Action(
                        operation=op, arguments={name: rng.choice(values)}
                    ).model_dump()
                    cases.append({"category": label + "-" + category, "actions": words})
    if spec["track"] == "A":
        if spec["family"] in {"rare", "delayed"}:
            prefix = (
                list(["abacaba", "bcabacaba", "cabbacabcab"][spec["variant"]]) + ["c"]
                if spec["family"] == "rare"
                else ["advance"] * [5, 7, 9][spec["variant"]] + ["commit"]
            )
            for _ in range(10):
                word = prefix + [rng.choice(list(target.actions)) for _ in range(64 - len(prefix))]
                cases.append(
                    {
                        "category": "challenge",
                        "actions": [target.actions[s].model_dump() for s in word],
                    }
                )
        return cases
    step = wallet_step if spec["track"] == "B" else inventory_step
    initial = (0, False) if spec["track"] == "B" else (0, 0)
    accesses, queue = {initial: []}, deque([initial])
    probes = [
        Action(operation=op, arguments={next(iter(schema)): v} if schema else {}).model_dump()
        for op, schema in contract["operations"].items()
        for v in range(1, 5)
        if schema
    ] + [
        Action(operation=op).model_dump()
        for op, schema in contract["operations"].items()
        if not schema
    ]
    while queue:
        state = queue.popleft()
        for action in probes:
            after, _ = step(state, action, spec["parameters"], contract)
            if after not in accesses:
                accesses[after] = accesses[state] + [action]
                queue.append(after)
    for state, access in accesses.items():
        for op, schema in contract["operations"].items():
            if not schema:
                continue
            name = next(iter(schema))
            for value in range(-8, 9):
                action = Action(operation=op, arguments={name: value}).model_dump()
                cases.append(
                    {
                        "category": "exhaustive",
                        "context": list(state),
                        "operation": op,
                        "value": value,
                        "probe_index": len(access),
                        "actions": access
                        + [
                            action,
                            Action(
                                operation="get_balance" if spec["track"] == "B" else "inspect"
                            ).model_dump(),
                        ],
                    }
                )
        op, name = ("deposit", "amount") if spec["track"] == "B" else ("stock", "quantity")
        for args in (
            {},
            {name: None},
            {name: True},
            {name: 1.0},
            {name: "1"},
            {name: 99999},
            {name: 1, "extra": 1},
        ):
            cases.append(
                {
                    "category": "validation",
                    "actions": access + [Action(operation=op, arguments=args).model_dump()],
                }
            )
    return cases
