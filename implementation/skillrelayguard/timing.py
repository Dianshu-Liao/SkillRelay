"""Diagnostic wall-clock spans; never used as authorization evidence."""

import argparse
from contextlib import contextmanager
import fcntl
from functools import wraps
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


VERSION = "module-timing-v1"


def append(path, record):
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            stream.write(json.dumps({"version": VERSION, **record}) + "\n")
    except OSError as error:
        print("Timing record unavailable: " + str(error), file=sys.stderr)


@contextmanager
def span(path, module, phase, stage=None, **metadata):
    identifier = uuid.uuid4().hex
    started = time.time()
    monotonic = time.monotonic()
    common = {"span_id": identifier, "module": module, "phase": phase,
              "stage": stage, "pid": os.getpid(), **metadata}
    append(path, {**common, "event": "start", "started_at": started})
    outcome = {"status": "completed"}
    try:
        yield outcome
    except BaseException as error:
        outcome.update(status="error", error_type=type(error).__name__)
        raise
    finally:
        append(path, {**common, "event": "end", "started_at": started,
                      "finished_at": time.time(), "elapsed_seconds": time.monotonic() - monotonic,
                      **outcome})


def timed(module, phase, locate):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            path, stage = locate(*args, **kwargs)
            with span(path, module, phase, stage, origin="host") as outcome:
                result = function(*args, **kwargs)
                if isinstance(result, dict) and result.get("checker_error"):
                    outcome["status"] = "checker_error"
                return result
        return wrapped
    return decorate


def attribution_location(run, stage, *args, **kwargs):
    return Path(run) / "guard/timings/host.jsonl", stage


def gate_location(gate, *args, **kwargs):
    return gate.directory.parent / "timings/host.jsonl", getattr(gate, "stage", None)


def policy_location(gate, stage, *args, **kwargs):
    return gate.directory.parent / "timings/host.jsonl", stage


def summarize(directory):
    starts = {}
    ends = {}
    malformed = 0
    for path in Path(directory).rglob("*.jsonl"):
        for line in path.read_text().splitlines():
            try:
                record = json.loads(line)
                target = starts if record["event"] == "start" else ends
                target[record["span_id"]] = record
            except (ValueError, KeyError):
                malformed += 1

    def union(records):
        merged = []
        for start, end in sorted((record["started_at"], record["finished_at"]) for record in records):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return sum(end - start for start, end in merged)

    return {"version": VERSION, "modules": {str(module): {
        "completed_spans": sum(record["module"] == module for record in ends.values()),
        "wall_union_seconds": union([record for record in ends.values() if record["module"] == module]),
        "unfinished_spans": sum(record["module"] == module for key, record in starts.items() if key not in ends)
        } for module in (1, 2, 3)},
        "wall_union_seconds": union(list(ends.values())), "malformed_records": malformed,
        "complete": bool(starts) and starts.keys() == ends.keys() and malformed == 0,
        "scope": "Union of recorded intervals, not sum of nested hooks/reviews. Excludes agent reasoning, CLI hook scheduling, background strace overhead, and snapshots. Hook records are agent-accessible diagnostic telemetry, never trusted evidence."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook", required=True)
    parser.add_argument("--module", choices=("2", "3"), required=True)
    args = parser.parse_args()
    raw = sys.stdin.buffer.read()
    try:
        event = json.loads(raw)
    except ValueError:
        event = {}
    directory = Path(os.environ.get("SKILLRELAYGUARD_TIMING_DIR", "/guard-timings"))
    with span(directory / "hooks.jsonl", int(args.module), "hook",
              os.environ.get("SKILLRELAYGUARD_STAGE"), origin="hook",
              hook_event=event.get("hook_event_name"), session_id=event.get("session_id"),
              tool_use_id=event.get("tool_use_id"), tool_name=event.get("tool_name")) as outcome:
        process = subprocess.run([sys.executable, args.hook], input=raw, stdout=subprocess.PIPE)
        outcome.update(returncode=process.returncode, status="completed" if process.returncode == 0 else "error")
        sys.stdout.buffer.write(process.stdout)
        sys.stdout.buffer.flush()
    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
