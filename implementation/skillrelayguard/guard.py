"""SkillRelayGuard runtime; no benchmark labels enter the online checker."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import shutil
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def append(path, record):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"timestamp": time.time(), **record}, ensure_ascii=False) + "\n")


def read_trace(path):
    reads, writes, executions = set(), set(), []
    pending = {}
    if not Path(path).exists():
        return {"reads": [], "writes": [], "executions": []}
    for line in Path(path).read_text(errors="replace").splitlines():
        process = re.match(r"(\d+)\s+", line)
        if process and line.endswith("<unfinished ...>"):
            pending[process[1]] = line.removesuffix("<unfinished ...>")
            continue
        resumed = re.match(r"(\d+)\s+<\.\.\. \w+ resumed>(.*)", line)
        if resumed:
            beginning = pending.pop(resumed[1], None)
            if beginning is None:
                continue
            line = beginning + resumed[2]
        if "execve(" in line and re.search(r"= 0$", line):
            executions.append(line)
        if "openat(" not in line and "open(" not in line:
            continue
        match = re.search(r"= \d+<(/workspace/[^>]+)>", line)
        if not match and re.search(r"= \d+(?:<[^>]+>)?$", line):
            match = re.search(r'open(?:at)?\([^"\n]*"(/workspace/[^"\n]+)"', line)
            if not match:
                relative_open = re.search(r'openat\([^,]*<(/workspace(?:/[^>]*)?)>, "([^"\n]+)"', line)
                if relative_open and not relative_open[2].startswith("/"):
                    path = str(Path(relative_open[1]) / relative_open[2])
                    match = re.match(r"(/workspace/.+)", path)
        if not match:
            continue
        relative = match[1][len("/workspace/"):]
        if "O_RDONLY" in line or "O_RDWR" in line:
            reads.add(relative)
        if any(flag in line for flag in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC")):
            writes.add(relative)
    return {"reads": sorted(reads), "writes": sorted(writes), "executions": executions}


def artifact_records(before, after, stage, task, trace):
    for name, digest in after.items():
        if before.get(name) == digest:
            continue
        yield {"event": "artifact_version", "path": name, "sha256": digest,
               "stage": stage, "user_task": task,
               "observed_stage_inputs": trace["reads"],
               "observed_skill_files": [entry for entry in trace["reads"] if entry.endswith("/SKILL.md")],
               "attribution": "stage-level observed dependencies, not field-level causality"}


def context_candidates(records, observed, stage):
    latest = {}
    for record in records:
        if record["stage"] != stage and record["path"] in observed:
            latest[record["path"]] = record
    return list(latest.values())


def checked_context(candidates, workspace):
    result = []
    root = Path(workspace).resolve()
    for record in candidates:
        path = root / record["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            continue
        result.append({key: record[key] for key in ("path", "sha256", "stage", "user_task", "observed_skill_files", "attribution")}
                      | {"observed_stage_inputs": record.get("observed_stage_inputs", [])}
                      | {key: record[key] for key in ("attribution_status", "skill_influences", "change_summary") if key in record})
    return result






class GuardController:
    def __init__(self, directory, tasks, project, model, ledger, mode="full"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory / "traces").mkdir(mode=0o700)
        timing_directory = self.directory / "timings"
        timing_directory.mkdir()
        (timing_directory / "hooks").mkdir(mode=0o777)
        (timing_directory / "hooks").chmod(0o777)
        self.tasks, self.project, self.model, self.ledger = tasks, project, model, ledger
        self.stage = "initial"
        self.records = []
        self.lock = threading.Lock()
        self.token = secrets.token_hex(24)
        if mode not in ("full", "context_only", "review_only"):
            raise ValueError("Unknown defense mode")
        self.mode = mode
        self.gate = None
        self.last_gate_feedback = None
        self.completed_tasks = []
        self.snapshots = []
        self.advisory_confirmations = {}
        self.advisory_pending = {}
        if mode != "context_only":
            from skillrelayguard.scoped_review import ScopedGate
            self.gate = ScopedGate(self.directory / "automatic", model, ledger)

    def start_stage(self, stage, task):
        self.advisory_confirmations.clear()
        self.advisory_pending.clear()
        self.stage = stage
        self.current_task = task
        self.last_gate_feedback = None
        append(self.directory / "provenance.jsonl", {"event": "session", "stage": stage, "user_task": task})
        if self.gate is not None:
            self.gate.start_stage(stage, task, self.project)

    def finish_stage(self, before, after, task):
        trace = read_trace(self.directory / "traces" / (self.stage + ".log"))
        append(self.directory / "provenance.jsonl", {"event": "observed_access", "stage": self.stage, **trace})
        records = list(artifact_records(before, after, self.stage, task, trace))
        for record in records:
            append(self.directory / "provenance.jsonl", record)
        self.records.extend(records)
        self.completed_tasks.append({"stage": self.stage, "user_task": task})
        self.snapshots.append((self.stage, self.directory.parent / (self.stage + "-workspace")))

    def dispatch(self, route, body):
        with self.lock:
            if route == "/pretool-error" and self.mode in ("full", "review_only"):
                if body.get("kind") == "adapter_input":
                    append(self.directory / "adapter-errors.jsonl", {"stage": self.stage,
                        "error": body["error"], "kind": "adapter_input", "security_verdict": False})
                    return {"accepted": True}
                append(self.directory / "decisions.jsonl", {"stage": self.stage,
                    "decision": "hold", "checker_error": body["error"], "review_origin": "pretool"})
                return {"accepted": True}
            if route == "/context-paths" and self.mode in ("full", "context_only", "review_only"):
                trace = read_trace(self.directory / "traces" / (self.stage + ".log"))
                paths = set(trace["reads"] + trace["writes"])
                for record in self.records:
                    if record["path"] in paths:
                        paths.update(record.get("observed_stage_inputs", []))
                return {"paths": sorted(paths)}
            if route == "/candidates":
                trace = read_trace(self.directory / "traces" / (self.stage + ".log"))
                if self.gate is not None and self.last_gate_feedback:
                    review_id = self.last_gate_feedback["verdict"].get("review_id")
                    if review_id:
                        with self.gate.pending_lock:
                            job = self.gate.pending.get(review_id)
                            if job and job["ready"].is_set():
                                result = job["result"]
                                if self.mode in ("full", "review_only"):
                                    result = self.advisory_feedback(result, self.advisory_pending[review_id])
                                self.last_gate_feedback = {"id": self.stage + ":" + review_id + ":completed",
                                                           "verdict": result}
                candidates = context_candidates(self.records, trace["reads"], self.stage)
                if self.mode in ("full", "context_only", "review_only"):
                    candidates = [record for record in candidates if record.get("attribution_status") == "supported"]
                return {"candidates": [] if self.mode == "review_only" else candidates,
                        "current_user_task": self.current_task, "gate_feedback": self.last_gate_feedback}
            if route == "/context-emitted":
                append(self.directory / "context-emitted.jsonl", {"stage": self.stage,
                    "evidence_type": "hook-reported output, not model acknowledgment", **body})
                return {"accepted": True}
            if route == "/context-observed":
                append(self.directory / "context.jsonl", {"stage": self.stage, "records": body["records"]})
                return {"accepted": True}
            if route == "/confirm" and self.mode in ("full", "review_only"):
                token = body.get("confirmation_token")
                saved = self.advisory_confirmations.pop(token, None) if isinstance(token, str) else None
                if saved is None:
                    raise ValueError("Unknown, expired or consumed confirmation token")
                append(self.directory / "advisory.jsonl", {"event": "agent_confirmed", "stage": self.stage,
                    "request_sha256": saved["request_sha256"], "recommendation": saved["verdict"]["decision"]})
                return {"confirmed": True, "route": saved["route"], "body": saved["body"]}
            if route != "/check":
                raise ValueError("Unsupported guard route")
            if self.mode not in ("full", "review_only"):
                raise ValueError("Operation checker disabled")
            context = {"current_stage": self.stage, "current_user_task": self.current_task,
                       "trusted_project_materials": self.project, "artifact_provenance": self.records}
            started = time.time()
            try:
                request = body["body"]
                if self.mode in ("full", "context_only", "review_only"):
                    from skillrelayguard.automatic import assemble_context
                    context = assemble_context(self.directory.parent / "seed", self.snapshots, self.records,
                                               body.get("observations", {}), self.current_task, self.completed_tasks)
                    request = {"request": request, "context": context}
                verdict = self.gate.check_bounded(body["route"], request)
            except Exception as error:
                verdict = {"decision": "hold", "reason": "Checker unavailable or invalid verdict",
                           "checker_error": f"{type(error).__name__}: {error}"}
            append(self.directory / "decisions.jsonl", {"stage": self.stage, "operation": body,
                   "checker_model": self.model, "elapsed_seconds": time.time() - started, **verdict})
            if self.mode in ("full", "review_only"):
                if verdict.get("review_pending"):
                    self.advisory_pending[verdict["review_id"]] = body
                verdict = self.advisory_feedback(verdict, body)
            if body.get("review_origin") == "pretool":
                append(self.directory / "pretool.jsonl", {"stage": self.stage,
                    "tool_use_id": body.get("tool_use_id"), "verdict": verdict,
                    "evidence_type": "preflight response; not proof of model acknowledgment"})
            if self.gate is not None and body.get("review_origin") != "pretool":
                self.last_gate_feedback = {"id": f"{self.stage}-{time.time_ns()}", "verdict": verdict}
            return verdict

    def advisory_feedback(self, verdict, request):
        feedback = {**verdict, "advisory_only": True, "accepted": False}
        if verdict.get("review_pending") or verdict.get("checker_error"):
            feedback["confirmation_available"] = False
            return feedback
        operation = {"stage": self.stage, "route": request["route"], "body": request["body"]}
        digest = hashlib.sha256(json.dumps(operation, sort_keys=True).encode()).hexdigest()
        token = next((key for key, value in self.advisory_confirmations.items() if value["request_sha256"] == digest), None)
        if token is None:
            token = secrets.token_hex(24)
            self.advisory_confirmations[token] = {**json.loads(json.dumps(operation)), "request_sha256": digest, "verdict": verdict}
            append(self.directory / "advisory.jsonl", {"event": "advice_ready", "stage": self.stage,
                "request_sha256": digest, "recommendation": verdict["decision"]})
        feedback.update(confirmation_available=True, confirmation_token=token, request_sha256=digest,
            confirmation_command="python3 /opt/guard/confirm.py --token " + token + " --receipt /workspace/advisory-confirmation.json",
            agent_choice="Nothing has been submitted. This is advice, not a veto. You may revise and resubmit for new advice, abandon, or explicitly confirm these exact reviewed bytes even if the recommendation is hold. The receipt path may be changed.")
        return feedback


def controller_handler(controller):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            try:
                prefix = "/" + controller.token
                if not self.path.startswith(prefix + "/"):
                    self.send_error(403)
                    return
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 2 * 1024 * 1024:
                    raise ValueError("Invalid size")
                result = controller.dispatch(self.path[len(prefix):], json.loads(self.rfile.read(size)))
                payload = json.dumps(result).encode()
                self.send_response(200)
            except Exception:
                payload = b'{"decision":"hold","reason":"Guard controller error"}'
                self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    return Handler


def guarded_environment(base, controller, controller_url, agent="codex"):
    from skillrelayguard.agents import hook_mount, hook_settings, prepare_command

    class Environment(base):
        def _start_service(self, name, alias, module, records, arguments, extra=None):
            if module == "receiver":
                hooks = hook_settings(agent, True, controller.mode in ("full", "review_only"))
                (controller.directory / "hooks.json").write_text(json.dumps(hooks))
                shutil.copyfile(Path(__file__), self.source_root / "guard.py")
                if controller.mode in ("full", "context_only", "review_only"):
                    shutil.copyfile(Path(__file__).with_name("observations.py"), self.source_root / "observations.py")
                module = "guard"
                arguments = [*arguments, "--controller", controller_url, "--mode", controller.mode]
                extra = [*(extra or []), "-v", self.workspace + ":/workspace:ro"]
            result = super()._start_service(name, alias, module, records, arguments, extra)
            if module == "guard":
                from skillrelayruntime.runtime import docker
                docker("network", "connect", "bridge", name)
            return result

        def agent_flags(self, name):
            flags = super().agent_flags(name)
            if "-stage-" not in name:
                return flags
            flags[flags.index("--user") + 1] = "0:0"
            flags += ["--cap-add", "SYS_PTRACE", "--cap-add", "SETUID", "--cap-add", "SETGID", "--cap-add", "CHOWN", "--cap-add", "DAC_OVERRIDE", "--cap-add", "DAC_READ_SEARCH",
                      "--mount", f"type=bind,source={controller.directory / 'traces'},target=/guard-traces",
                      "--mount", f"type=bind,source={controller.directory / 'hooks.json'},target={hook_mount(agent)},readonly",
                      "-e", f"SKILLRELAYGUARD_AGENT={agent}",
                      "--mount", f"type=bind,source={controller.directory / 'timings/hooks'},target=/guard-timings",
                      "--mount", f"type=bind,source={Path(__file__).with_name('timing.py')},target=/opt/guard/timing.py,readonly",
                      "--mount", f"type=bind,source={Path(__file__).with_name('guard_hook.py')},target=/opt/guard/hook.py,readonly"]
            if agent == "gemini":
                flags += ["--tmpfs", "/guard-system:rw,nosuid,nodev,size=1m,mode=755",
                          "-e", "GEMINI_CLI_SYSTEM_SETTINGS_PATH=/guard-system/settings.json"]
            if controller.mode in ("full", "review_only"):
                flags += ["--mount", f"type=bind,source={Path(__file__).with_name('advisory_confirm.py')},target=/opt/guard/confirm.py,readonly"]
            if controller.mode in ("full", "review_only"):
                flags += ["--mount", f"type=bind,source={Path(__file__).with_name('pretool_hook.py')},target=/opt/guard/pretool_hook.py,readonly",
                          "--mount", f"type=bind,source={Path(__file__).with_name('pretool_submit.py')},target=/opt/guard/submit.py,readonly"]
            return flags

        def execute(self, command, stage, timeout=600):
            if stage.startswith("stage-"):
                command = ["env", "SKILLRELAYGUARD_STAGE=" + stage, *prepare_command(agent, command)]
                command = ["strace", "-f", "-qq", "-yy", "-s", "4096", "-e", "trace=%file",
                           "-o", "/guard-traces/" + stage + ".log", "-u", "node", *command]
                command = ["sh", "-c", 'chown 1000:1000 "$HOME/.codex" "$HOME/.claude"; exec "$@"', "guard-bootstrap", *command]
                if agent == "gemini":
                    command = ["sh", "-c", 'cp /opt/guard/settings.json /guard-system/settings.json; chmod 644 /guard-system/settings.json; exec "$@"',
                               "gemini-settings-bootstrap", *command]
            return super().execute(command, stage, timeout)
    return Environment


def post(url, body, timeout=26):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def receiver_handler(evidence, controller_url, workspace, mode="full"):
    from skillrelayruntime.receiver import handler_for
    base = handler_for(Path(evidence))
    lock = threading.Lock()

    class Handler(base):
        def do_GET(self):
            if self.path != "/guard-context":
                return super().do_GET()
            try:
                response = post(controller_url + "/candidates", {})
                records = checked_context(response["candidates"], workspace)
                if records:
                    post(controller_url + "/context-observed", {"records": records})
                self.respond(200, {"records": records, "current_user_task": response["current_user_task"],
                                   "mode": mode, "gate_feedback": response.get("gate_feedback")})
            except Exception:
                self.respond(503, {"error": "provenance unavailable"})

        def do_POST(self):
            if self.path == "/guard-pretool-error" and mode in ("full", "review_only"):
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 8192 or self.headers.get("Transfer-Encoding"):
                        raise ValueError("Invalid pre-tool error report")
                    error = json.loads(self.rfile.read(size))
                    self.respond(200, post(controller_url + "/pretool-error", error))
                except (ValueError, KeyError, TypeError, OSError):
                    self.respond(503, {"error": "Could not record pre-tool error"})
                return
            if self.path == "/guard-preflight" and mode in ("full", "review_only"):
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 262144 or self.headers.get("Transfer-Encoding"):
                        raise ValueError("Invalid preflight framing")
                    operation = json.loads(self.rfile.read(size))
                    if operation.get("route") not in ("/deliver", "/preview") or not isinstance(operation.get("body"), dict):
                        raise ValueError("Invalid preflight operation")
                    from .observations import observe_files
                    paths = post(controller_url + "/context-paths", {})["paths"]
                    paths += operation.get("input_paths", [])
                    request = {"route": operation["route"], "body": operation["body"],
                               "observations": observe_files(workspace, paths), "review_origin": "pretool",
                               "tool_use_id": operation.get("tool_use_id")}
                    verdict = post(controller_url + "/check", request, timeout=35)
                    self.respond(200, verdict)
                except (ValueError, KeyError, TypeError, OSError):
                    self.respond(503, {"checker_error": "Preflight unavailable", "confirmation_available": False})
                return
            if self.path == "/guard-confirm" and mode in ("full", "review_only"):
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 4096 or self.headers.get("Transfer-Encoding"):
                        raise ValueError("Invalid confirmation request")
                    confirmation = json.loads(self.rfile.read(size))
                    if set(confirmation) != {"confirmation_token"}:
                        raise ValueError("Confirmation must reference reviewed bytes, not supply replacement content")
                    approved = post(controller_url + "/confirm", confirmation)
                    with lock:
                        append(evidence, {"event": "delivery" if approved["route"] == "/deliver" else "preview_call", "body": approved["body"]})
                    self.respond(200, {"accepted": True, "agent_confirmed": True,
                                       "sha256": approved["body"].get("sha256")})
                except (ValueError, KeyError, OSError):
                    self.respond(409, {"accepted": False, "error": "Invalid or expired confirmation; submit for a new review"})
                return
            if self.path == "/guard-context-emitted":
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 262144:
                        raise ValueError("Invalid log size")
                    body = json.loads(self.rfile.read(size))
                    self.respond(200, post(controller_url + "/context-emitted", body))
                except (ValueError, OSError):
                    self.respond(503, {"error": "context logging unavailable"})
                return
            if mode not in ("full", "review_only"):
                return super().do_POST()
            if self.path not in ("/deliver", "/preview"):
                self.respond(404, {"error": "unknown route"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("Invalid request framing")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Expected object")
                request = {"route": self.path, "body": body}
                if mode in ("full", "context_only", "review_only"):
                    from .observations import observe_files
                    paths = post(controller_url + "/context-paths", {})["paths"]
                    request["observations"] = observe_files(workspace, paths)
                verdict = post(controller_url + "/check", request, timeout=140)
                self.respond(409, {"accepted": False, "review_only": True, "guard": verdict})
            except (ValueError, KeyError, OSError, urllib.error.URLError):
                self.respond(403, {"accepted": False, "error": "guard could not authorize operation"})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--controller", required=True)
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--mode", choices=("full", "context_only", "review_only"), default="full")
    args = parser.parse_args()
    if args.mode in ("full", "context_only", "review_only"):
        from .observations import observe_files
    ThreadingHTTPServer(("0.0.0.0", 8080), receiver_handler(args.evidence, args.controller, args.workspace, args.mode)).serve_forever()


if __name__ == "__main__":
    main()
