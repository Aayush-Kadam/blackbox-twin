"""Bounded M6 training adapters using existing physical accounting and learner engines."""

import json
import random
import time

from aalpy.oracles import StatePrefixEqOracle

from .benchmark import Checkpoints, CheckpointSession, benchmark_recorder
from .contracts import Action, BehavioralModel, QueryBudget
from .guards import GuardedModel
from .learning import learn
from .m5 import discover, make_target, twin_runner, write
from .m51 import resolving_probe, shortest_access
from .oracle import BudgetExhausted, OracleFailure, ProcessOracle, Session
from .planner_oracles import ReplayCacheSUL, SelectionOracle
from .refinement import phase_costs
from .support import SupportedModel, compile_support
from .synthesis import generate_twin
from .typed import word_keys
from .typed_learning import (
    choose_boundary_experiments,
    initialize,
    observations,
    probe,
    save_model,
    shrink_typed,
)


class IsolatedRandom:
    """Keep native equivalence-query randomness separate from learner randomness."""

    def find_cex(self, hypothesis):
        previous = random.getstate()
        random.setstate(self.training_state)
        try:
            return super().find_cex(hypothesis)
        finally:
            self.training_state = random.getstate()
            random.setstate(previous)


class StreamSelection(IsolatedRandom, SelectionOracle):
    def __init__(self, *args, training_seed, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_state = random.Random(training_seed).getstate()


class StreamPrefix(IsolatedRandom, StatePrefixEqOracle):
    def __init__(self, alphabet, sul, training_seed):
        super().__init__(alphabet, sul, walks_per_state=1, walk_len=3)
        self.training_state = random.Random(training_seed).getstate()


def fallback(reason, finite=None):
    return {
        "schema_version": 4,
        "reason": reason,
        "finite": finite,
        "model_class": "finite-concrete" if finite else "unsupported",
    }


def export_portable(model, path):
    """Version 4 is an explicit concrete-alphabet adapter, not a new guarded grammar."""
    classes = {1: BehavioralModel, 2: GuardedModel, 3: SupportedModel}
    if model["schema_version"] in classes:
        generate_twin(classes[model["schema_version"]].model_validate(model), path)
        return
    if model["schema_version"] != 4:
        raise ValueError("Unknown benchmark model format")
    source = """import json,sys
MODEL=json.loads(DATA)
inner=MODEL.get("finite")
state=inner["initial_state"] if inner else None
keys={json.dumps(a,sort_keys=True,separators=(",",":")):k
      for k,a in inner["actions"].items()} if inner else {}
for line in sys.stdin:
 try:
  request=json.loads(line)
  if request=={"control":"reset"}:
   state=inner["initial_state"] if inner else None
   output={"control":"reset","ok":True}
  else:
   symbol=keys.get(json.dumps(request,sort_keys=True,separators=(",",":")))
   if state is None or symbol is None:
    state=None
    output={"bbt_unsupported":True,"support_status":"UNSUPPORTED","reason":MODEL["reason"]}
   else:
    edge=inner["transitions"][state][symbol]
    output=edge["output"]["payload"]
    state=edge["next_state"]
 except (ValueError,TypeError,KeyError):
  state=None
  output={"bbt_unsupported":True,"support_status":"UNSUPPORTED","reason":"malformed_request"}
 print(json.dumps(output),flush=True)
"""
    path.write_text(source.replace("DATA", repr(json.dumps(model))), encoding="utf-8")


def finite_train(
    target, script, folder, ceilings, method, learner_seed, training_seed, concrete=False
):
    folder.mkdir(parents=True)
    recorder = benchmark_recorder(
        folder / "observations.sqlite",
        {
            "method": method,
            "learner_seed": learner_seed,
            "training_seed": training_seed,
            "ceilings": ceilings,
        },
    )
    session = CheckpointSession(
        ProcessOracle(script),
        target,
        QueryBudget(
            max_actions=max(ceilings), max_resets=3000, total_seconds=120.0, max_sequence_length=100
        ),
        recorder,
        "reset-validation",
    )
    tracker = Checkpoints(session, folder, ceilings)
    session.tracker = tracker
    delegates, status, stats = [], "failed", {}
    started = time.perf_counter()

    def factory(alphabet, sul):
        oracle = StreamSelection(
            alphabet, sul, method, training_seed, max_length=12, training_seed=training_seed
        )
        delegates.append(oracle)
        return oracle

    try:
        session.verify_reset()
        session.phase = "membership"
        _, stats = learn(
            session,
            folder / "latest.json",
            seed=learner_seed,
            equivalence_factory=factory,
            sul_factory=ReplayCacheSUL,
            checkpoint_hook=tracker.on_model,
        )
        status = "completed"
    except BudgetExhausted as error:
        status = (
            "action_budget" if str(error) == "physical_action_budget" else "failed:" + str(error)
        )
    except Exception as error:
        status = "failed:" + type(error).__name__ + ":" + str(error)
    except BaseException:
        status = "interrupted"
        raise
    finally:
        session.post(status)
        cleanup_error = None
        try:
            session.oracle.close()
        except Exception as error:
            cleanup_error = type(error).__name__ + ":" + str(error)
            status = "failed:cleanup:" + cleanup_error
        for ceiling in ceilings:
            if ceiling not in tracker.points:
                tracker.capture(ceiling, session.costs.actions)
        points = []
        for point in sorted(tracker.points.values(), key=lambda p: p["ceiling"]):
            model = (
                json.loads((folder / point["model"]).read_text())
                if point["model"]
                else fallback("no_complete_hypothesis")
            )
            if concrete and model["schema_version"] == 1:
                model = fallback("outside_concrete_alphabet_or_unknown_state", model)
            filename = f"scored-{point['ceiling']}.json"
            write(folder / filename, model)
            twin = f"twin-{point['ceiling']}.py"
            export_portable(model, folder / twin)
            points.append({**point, "model": filename, "twin": twin})
        replay = getattr(session, "replay_cache", None)
        receipt = {
            "complete": status != "interrupted",
            "status": status,
            "costs": session.costs.model_dump(),
            "phase_costs": phase_costs(recorder),
            "points": points,
            "cache_prefix_outputs": replay.cache_actions if replay else 0,
            "cache_traces": replay.cache_traces if replay else 0,
            "counterexamples": delegates[0].counterexamples if delegates else [],
            "search_bookkeeping_seconds": delegates[0].planning_seconds if delegates else 0,
            "statistics": stats,
            "cleanup_error": cleanup_error,
            "wall_seconds": time.perf_counter() - started,
        }
        recorder.close(status)
        write(folder / "receipt.json", receipt)
    return receipt


def unsupported_train(folder, budget, reason):
    """Compatibility failure has no fabricated training cost or efficiency success."""
    folder.mkdir(parents=True)
    recorder = benchmark_recorder(folder / "observations.sqlite", {"compatibility": reason})
    recorder.close("model_class_unsupported")
    model = fallback(reason)
    write(folder / "model.json", model)
    export_portable(model, folder / "twin.py")
    receipt = {
        "complete": True,
        "status": "model_class_unsupported",
        "costs": {"actions": 0, "resets": 0, "sequences": 0, "oracle_seconds": 0},
        "wall_seconds": 0,
        "phase_costs": {},
        "points": [
            {"ceiling": budget, "actual_actions": 0, "model": "model.json", "twin": "twin.py"}
        ],
    }
    write(folder / "receipt.json", receipt)
    return receipt


def typed_train(contract, script, folder, budget, method, learner_seed, training_seed):
    folder.mkdir(parents=True)
    contract = json.loads(json.dumps(contract))
    contract["training_budget"] = {"max_actions": budget, "max_resets": 3000, "total_seconds": 120}
    recorder = benchmark_recorder(
        folder / "observations.sqlite",
        {
            "method": method,
            "contract": contract,
            "learner_seed": learner_seed,
            "training_seed": training_seed,
        },
    )
    session = Session(
        ProcessOracle(script),
        make_target("m6-public-wallet"),
        QueryBudget(
            max_actions=budget, max_resets=3000, total_seconds=120.0, max_sequence_length=100
        ),
        recorder,
    )
    status, started, revision = "failed", time.perf_counter(), 0
    receipt = {"counterexamples": [], "probes": [], "regressions": {"tested": 0, "passed": 0}}
    current = None

    def persist():
        nonlocal revision, current
        number = revision
        revision += 1
        rows, accesses = observations(session, contract)
        if method == "hardened":
            model = compile_support(
                contract, rows, [{"kind": "M6 bounded run", "revision": revision}]
            )
            destination = folder / f"revision-{number:03}"
            destination.mkdir()
            write(destination / "model.json", model.model_dump())
            generate_twin(model, destination / "twin.py")
        else:
            model, accesses = save_model(
                session, contract, folder / f"revision-{number:03}", number
            )
            destination = folder / f"revision-{number:03}"
        current = destination
        return model, accesses

    try:
        initialize(
            session,
            contract,
            folder / "initial",
            seed=learner_seed,
            equivalence_factory=lambda alphabet, sul: StreamPrefix(alphabet, sul, training_seed),
        )
        model, accesses = persist()
        if method == "adaptive":
            with twin_runner(session, current / "twin.py", folder) as runner:
                found = discover(runner, model, accesses, contract)
                if found:
                    session.phase = "counterexample-minimization"
                    reduced, details = shrink_typed(runner, found, contract)
                    receipt["counterexamples"].append(reduced.model_dump())
                    write(folder / "counterexample.json", details)
            for _ in range(3):
                model, accesses = persist()
                if not choose_boundary_experiments(session, model, accesses, 16):
                    break
        elif method == "hardened":
            rng = random.Random(training_seed)
            for _ in range(12):
                rows, _ = observations(session, contract)
                choice = resolving_probe(
                    model, shortest_access(rows), set(contract["reserved_evaluation_values"]), rng
                )
                if choice is None:
                    break
                cost, _, key, access, action = choice
                if session.costs.actions + cost > budget:
                    break
                session.phase = "guard-discrimination"
                before = session.costs.actions
                output = probe(session, access, action)
                receipt["probes"].append(
                    {
                        "key": key,
                        "cost": session.costs.actions - before,
                        "output": output[-1].payload,
                    }
                )
                model, accesses = persist()
        if method != "fixed-grid":
            model, accesses = persist()
            with twin_runner(session, current / "twin.py", folder) as runner:
                session.phase = "regression-verification"
                rows, _ = observations(session, contract)
                for row in rows:
                    if session.costs.actions >= budget:
                        raise BudgetExhausted("physical_action_budget")
                    actions = [Action.model_validate(a) for a in row["access"] + [row["action"]]]
                    result = runner.run(word_keys(session.target, actions))
                    if result.status == "budget_exhausted":
                        raise BudgetExhausted(result.detail or "physical_action_budget")
                    if result.status in {
                        "timeout",
                        "crash",
                        "reset_failure",
                        "infrastructure_failure",
                    }:
                        raise OracleFailure(result.status + ":" + str(result.detail))
                    receipt["regressions"]["tested"] += 1
                    receipt["regressions"]["passed"] += result.status == "agreement"
        status = "completed"
    except BudgetExhausted as error:
        status = (
            "action_budget" if str(error) == "physical_action_budget" else "failed:" + str(error)
        )
    except (ValueError, OracleFailure) as error:
        status = ("model_class_failure:" if isinstance(error, ValueError) else "failed:") + str(
            error
        )
    except Exception as error:
        status = "failed:" + type(error).__name__ + ":" + str(error)
    except BaseException:
        status = "interrupted"
        raise
    finally:
        session.post(status)
        # Fit only already committed observations; this never acquires future oracle data.
        if status != "interrupted":
            try:
                persist()
            except (ValueError, KeyError):
                pass
        try:
            session.oracle.close()
        except Exception as error:
            receipt["cleanup_error"] = type(error).__name__ + ":" + str(error)
            status = "failed:cleanup:" + receipt["cleanup_error"]
        model_data = (
            fallback("insufficient_or_unrepresentable_observations")
            if current is None
            else json.loads((current / "model.json").read_text())
        )
        write(folder / "scored.json", model_data)
        export_portable(model_data, folder / "twin.py")
        receipt.update(
            complete=status != "interrupted",
            status=status,
            costs=session.costs.model_dump(),
            phase_costs=phase_costs(recorder),
            revisions=revision,
            points=[
                {
                    "ceiling": budget,
                    "actual_actions": session.costs.actions,
                    "model": "scored.json",
                    "twin": "twin.py",
                }
            ],
            wall_seconds=time.perf_counter() - started,
            cache_note="common initial ReplayCacheSUL; subsequent typed probes replay physically",
        )
        recorder.close(status)
        write(folder / "receipt.json", receipt)
    return receipt
