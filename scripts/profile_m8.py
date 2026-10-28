"""Bounded Windows process-tree profiling using native read-only resource counters.

Samples aggregate working sets (shared pages may be counted more than once), not unique
physical RAM or an exact instantaneous maximum. Browser renderer memory is excluded.
"""

import argparse
import ctypes as c
import http.client
import json
import signal
import statistics
import subprocess
import sys
import time
from ctypes import wintypes as w
from pathlib import Path


class Entry(c.Structure):
    _fields_ = [
        (n, t)
        for n, t in [
            ("size", w.DWORD),
            ("usage", w.DWORD),
            ("pid", w.DWORD),
            ("heap", c.c_void_p),
            ("module", w.DWORD),
            ("threads", w.DWORD),
            ("parent", w.DWORD),
            ("priority", w.LONG),
            ("flags", w.DWORD),
            ("name", w.WCHAR * 260),
        ]
    ]


class Memory(c.Structure):
    _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [
        (n, c.c_size_t)
        for n in (
            "peak_rss",
            "rss",
            "peak_paged",
            "paged",
            "peak_nonpaged",
            "nonpaged",
            "pagefile",
            "peak_pagefile",
            "private",
        )
    ]


class Native:
    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("This measurement implementation is Windows-only")
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.k.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
        self.k.CreateToolhelp32Snapshot.restype = w.HANDLE
        self.k.Process32FirstW.argtypes = self.k.Process32NextW.argtypes = [
            w.HANDLE,
            c.POINTER(Entry),
        ]
        self.k.OpenProcess.argtypes, self.k.OpenProcess.restype = (
            [w.DWORD, w.BOOL, w.DWORD],
            w.HANDLE,
        )
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
        self.k.K32GetProcessMemoryInfo.argtypes = [w.HANDLE, c.POINTER(Memory), w.DWORD]
        self.k.TerminateProcess.argtypes = [w.HANDLE, w.UINT]

    def tree(self, root):
        handle = self.k.CreateToolhelp32Snapshot(2, 0)
        if handle == c.c_void_p(-1).value:
            raise c.WinError(c.get_last_error())
        parents, item = {}, Entry()
        item.size = c.sizeof(item)
        try:
            ok = self.k.Process32FirstW(handle, c.byref(item))
            while ok:
                parents[item.pid] = item.parent
                ok = self.k.Process32NextW(handle, c.byref(item))
        finally:
            self.k.CloseHandle(handle)
        owned = [root] if root in parents else []
        for pid in owned:
            owned.extend(p for p, parent in parents.items() if parent == pid and p not in owned)
        return owned

    def counters(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            values = [w.FILETIME() for _ in range(4)]
            if not self.k.GetProcessTimes(handle, *[c.byref(x) for x in values]):
                return None

            def ticks(x):
                return (x.dwHighDateTime << 32) | x.dwLowDateTime

            if ticks(values[1]):
                # A retained process handle can expose counters after Windows records exit.
                return None
            memory = Memory()
            memory.cb = c.sizeof(memory)
            if not self.k.K32GetProcessMemoryInfo(handle, c.byref(memory), memory.cb):
                return None
            return {
                "creation": ticks(values[0]),
                "rss": memory.rss,
                "private": memory.private,
                "cpu_seconds": (ticks(values[2]) + ticks(values[3])) / 1e7,
            }
        finally:
            self.k.CloseHandle(handle)

    def terminate(self, pid, creation):
        # Avoid terminating an unrelated process after PID reuse.
        current = self.counters(pid)
        if not current or current["creation"] != creation:
            return
        handle = self.k.OpenProcess(1, False, pid)
        if handle:
            try:
                self.k.TerminateProcess(handle, 0)
            finally:
                self.k.CloseHandle(handle)


def request(port, path, post=False):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request(
            "POST" if post else "GET",
            path,
            body="{}" if post else None,
            headers={"X-BBT-Local": "1", "Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read(2_000_000))
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}: {body}")
        return body
    finally:
        connection.close()


def disk(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) if root.exists() else 0


def profile(python, project, out, port, repeat):
    out.mkdir(parents=True)
    working = out / "working"
    working.mkdir()
    native, samples, seen, unavailable, jobs = Native(), [], {}, 0, []
    log = (out / "server.log").open("w", encoding="utf-8")
    started = time.perf_counter()
    process = subprocess.Popen(
        [
            str(python),
            "-m",
            "blackbox_twin.workbench",
            "--project",
            str(project),
            "--runs",
            str(out / "runs"),
            "--port",
            str(port),
        ],
        cwd=working,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    def sample(stage):
        nonlocal unavailable
        pids, values = native.tree(process.pid), []
        for pid in pids:
            value = native.counters(pid)
            if value is None:
                unavailable += 1
                continue
            identity = str(pid) + ":" + str(value["creation"])
            seen[identity] = {"pid": pid, **value}
            values.append(value)
        samples.append(
            {
                "seconds": time.perf_counter() - started,
                "stage": stage,
                "rss": sum(v["rss"] for v in values),
                "private": sum(v["private"] for v in values),
                "processes": len(pids),
                "measured": len(values),
            }
        )

    graceful, failure = False, None
    try:
        deadline = started + 30
        while True:
            sample("startup")
            try:
                request(port, "/api/experiments")
                break
            except (OSError, ValueError):
                if time.perf_counter() > deadline or process.poll() is not None:
                    raise RuntimeError("Local server did not become ready") from None
                time.sleep(0.05)
        startup = time.perf_counter() - started
        for _ in range(20):
            sample("idle")
            time.sleep(0.05)
        for index in range(repeat):
            job = request(port, "/api/demo", post=True)
            deadline, next_poll = time.perf_counter() + 220, 0
            while True:
                sample(f"demo-{index}")
                if time.perf_counter() >= next_poll:
                    job = request(port, "/api/jobs/" + job["id"])
                    next_poll = time.perf_counter() + 0.25
                    if job["status"] != "running":
                        if job["status"] != "completed":
                            raise RuntimeError(str(job))
                        jobs.append(job)
                        break
                if time.perf_counter() > deadline:
                    raise RuntimeError("Bounded profiling watchdog expired")
                time.sleep(0.05)
    except Exception as exc:
        failure = type(exc).__name__ + ": " + str(exc)
    finally:
        shutdown = time.perf_counter()
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
            process.wait(timeout=5)
            graceful = True
        except (OSError, subprocess.TimeoutExpired):
            for value in reversed(list(seen.values())):
                native.terminate(value["pid"], value["creation"])
            process.wait(timeout=5)
        shutdown_seconds = time.perf_counter() - shutdown
        log.close()
    drain_deadline = time.perf_counter() + 2
    while True:
        alive = [
            value["pid"]
            for value in seen.values()
            if (current := native.counters(value["pid"]))
            and current["creation"] == value["creation"]
        ]
        if not alive or time.perf_counter() >= drain_deadline:
            break
        time.sleep(0.05)
    idle = [v["rss"] for v in samples if v["stage"] == "idle"]
    report = {
        "status": "PASS" if not failure and not alive and len(jobs) == repeat else "FAIL",
        "error": failure,
        "python": str(python),
        "platform": sys.platform,
        "method": "Win32 Toolhelp process ancestry + GetProcessMemoryInfo + GetProcessTimes",
        "sampling_target_seconds": 0.05,
        "samples": len(samples),
        "counter_race_or_access_failures": unavailable,
        "peak_sampled_aggregate_rss_bytes": max((v["rss"] for v in samples), default=0),
        "peak_sampled_aggregate_private_commit_bytes": max(
            (v["private"] for v in samples), default=0
        ),
        "idle_median_rss_bytes": statistics.median(idle) if idle else None,
        "observed_cpu_seconds": sum(v["cpu_seconds"] for v in seen.values()),
        "peak_sampled_process_count": max((v["processes"] for v in samples), default=0),
        "startup_to_http_ready_seconds": locals().get("startup"),
        "shutdown_seconds": shutdown_seconds,
        "graceful_signal_shutdown": graceful,
        "remaining_owned_pids": alive,
        "sampled_process_identities": list(seen.values()),
        "temporary_directory_bytes_after_cleanup": disk(working / "work/processes"),
        "remaining_temporary_directories": len(list((working / "work/processes").glob("bbt-*"))),
        "experiment_artifact_bytes": disk(out / "runs"),
        "jobs": jobs,
        "measurement_limits": [
            "Sampling can miss short peaks and short-lived children.",
            "RSS sums may double-count shared pages; private commit is not resident physical RAM.",
            "CPU totals use last observed counters and may miss final increments.",
            "Browser renderer memory is excluded; profiler overhead affects runtime.",
            "These measurements do not enforce OS memory or process-tree limits.",
        ],
    }
    (out / "samples.json").write_text(json.dumps(samples), encoding="utf-8")
    (out / "profile.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "jobs"}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--repeat", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    raise SystemExit(
        profile(
            args.python.resolve(),
            args.project.resolve(),
            args.out.resolve(),
            args.port,
            args.repeat,
        )
    )
