"""Bounded local JSON-lines transport. This is a process boundary, not a sandbox."""

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import suppress
from pathlib import Path

from .contracts import Action, Costs, Observation, QueryBudget, Target


class OracleFailure(RuntimeError):
    pass


class BudgetExhausted(RuntimeError):
    pass


def oracle_environment():
    """Trusted local fixtures need OS/locale paths, not the developer's credentials.

    This reduces accidental secret inheritance; it does not restrict same-user file or
    network access and is not an OS sandbox. Custom fixtures needing extra configuration
    must make that requirement explicit rather than inheriting the whole environment.
    """
    allowed = ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "LANG", "LC_ALL", "TZ")
    return {key: os.environ[key] for key in allowed if key in os.environ}


def _read_responses(stream, responses, limit):
    try:
        while True:
            line = stream.readline(limit + 1)
            if not line:
                responses.put(OracleFailure("process_eof"), timeout=1)
                return
            if len(line) > limit:
                responses.put(OracleFailure("response_too_large"), timeout=1)
                return
            responses.put(line, timeout=1)
    except (OSError, ValueError, queue.Full):
        return


class ProcessOracle:
    def __init__(self, script: Path, timeout=2.0, max_response_bytes=65536, scratch_root=None):
        self.script = script.resolve(strict=True)
        self.timeout = timeout
        scratch = Path(scratch_root) if scratch_root else Path.cwd() / "work" / "processes"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="bbt-", dir=scratch)
        self.responses = queue.Queue(maxsize=2)
        # No shell; no inherited Python import path; empty working directory.
        self.process = subprocess.Popen(
            [sys.executable, "-I", "-u", str(self.script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=self.temp.name,
            shell=False,
            env=oracle_environment(),
        )
        self.reader = threading.Thread(
            target=_read_responses,
            args=(self.process.stdout, self.responses, max_response_bytes),
            daemon=True,
        )
        self.reader.start()
        self.closed = False
        self.cleanup_error = None

    def _close_after_failure(self, primary):
        try:
            self.close()
        except Exception as cleanup:
            self.cleanup_error = f"{type(cleanup).__name__}: {cleanup}"
            # Preserve the protocol failure and make the cleanup failure visible in evidence.
            primary.args = (f"{primary} [cleanup_failure: {self.cleanup_error}]",)

    def _exchange(self, request):
        if self.closed:
            raise OracleFailure("closed_process")
        encoded = (json.dumps(request) + "\n").encode()
        if len(encoded) > 1024:
            raise OracleFailure("request_too_large")
        try:
            self.process.stdin.write(encoded)
            self.process.stdin.flush()
            item = self.responses.get(timeout=self.timeout)
            if isinstance(item, Exception):
                raise item
            result = json.loads(item)
            if not isinstance(result, dict):
                raise ValueError("Response must be a JSON object")
            return result
        except queue.Empty as exc:
            primary = OracleFailure("response_timeout")
            self._close_after_failure(primary)
            raise primary from exc
        except (OSError, ValueError, OracleFailure) as exc:
            crashed = isinstance(exc, OSError) and self.process.poll() is not None
            primary = OracleFailure(
                "process_eof: broken subprocess pipe" if crashed else f"transport_failure: {exc}"
            )
            self._close_after_failure(primary)
            raise primary from exc

    def reset(self):
        response = self._exchange({"control": "reset"})
        if response != {"control": "reset", "ok": True}:
            primary = OracleFailure("reset_not_acknowledged")
            self._close_after_failure(primary)
            raise primary
        return response

    def step(self, action: Action):
        return Observation(payload=self._exchange(action.model_dump()))

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=2)
        # Windows may re-raise the earlier broken-pipe error while flushing close().
        with suppress(OSError):
            self.process.stdin.close()
        self.reader.join(timeout=2)
        self.process.stdout.close()
        for attempt in range(5):
            try:
                self.temp.cleanup()
                break
            except PermissionError as exc:
                if getattr(exc, "winerror", None) not in (32, 33) or attempt == 4:
                    raise
                time.sleep(0.05 * (2**attempt))


class Session:
    """Physical costs are counted here, below any learning cache."""

    def __init__(self, oracle, target: Target, budget: QueryBudget, recorder, phase="training"):
        self.oracle, self.target, self.budget, self.recorder = oracle, target, budget, recorder
        self.phase = phase
        self.costs = Costs()
        self.start = time.monotonic()
        self.exp = None
        self.word = []

    def check(self, kind):
        if time.monotonic() - self.start >= self.budget.total_seconds:
            raise BudgetExhausted("total_wall_clock")
        if kind == "action" and self.costs.actions >= self.budget.max_actions:
            raise BudgetExhausted("physical_action_budget")
        if kind == "reset" and self.costs.resets >= self.budget.max_resets:
            raise BudgetExhausted("reset_budget")

    def _call(self, kind, request, fn):
        self.check(kind)
        if kind == "action":
            self.costs.actions += 1
        else:
            self.costs.resets += 1
        # Bound an in-flight call by both remaining total time and per-query timeout.
        self.oracle.timeout = min(
            self.budget.query_timeout_seconds,
            self.budget.total_seconds - (time.monotonic() - self.start),
        )
        started = time.monotonic()
        result, status = None, "ok"
        try:
            result = fn()
            return result
        except Exception as exc:
            status = type(exc).__name__ + ": " + str(exc)
            raise
        finally:
            elapsed = time.monotonic() - started
            self.costs.oracle_seconds += elapsed
            payload = result.model_dump() if isinstance(result, Observation) else result
            self.recorder.event(self.exp, kind, request, payload, elapsed, status)

    def pre(self):
        self.post()
        self.check("reset")
        self.exp = self.recorder.begin(self.phase)
        self.word = []
        self.costs.sequences += 1
        try:
            self._call("reset", {"control": "reset"}, self.oracle.reset)
        except Exception:
            self.post("failed")
            raise

    def step(self, symbol):
        if self.exp is None:
            raise OracleFailure("step_without_reset")
        if len(self.word) >= self.budget.max_sequence_length:
            raise BudgetExhausted("sequence_length")
        action = self.target.actions[symbol]
        self.word.append(symbol)
        try:
            return self._call("action", action.model_dump(), lambda: self.oracle.step(action))
        except Exception:
            self.post("failed")
            raise

    def post(self, status="completed"):
        if self.exp is not None:
            self.recorder.finish(self.exp, self.word, status)
            self.exp = None

    def trace(self, word):
        self.pre()
        try:
            outputs = [self.step(s) for s in word]
        except BaseException:
            self.post("failed")
            raise
        self.post()
        return outputs

    def verify_reset(self):
        # Repeat the same distinguishing probe from independently acknowledged resets.
        probe = list(self.target.actions)
        if self.trace(probe) != self.trace(probe):
            raise OracleFailure("reset_or_determinism_probe_mismatch")
