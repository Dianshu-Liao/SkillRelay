from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


MODELS = {
    "gemini": os.environ.get("SKILLRELAYBENCH_GEMINI_MODEL", "gemini-3.6-flash"),
    "claude": os.environ.get("SKILLRELAYBENCH_CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
    "codex": os.environ.get("SKILLRELAYBENCH_CODEX_MODEL", "gpt-5.3-codex"),
}


def claude_auth_ready(min_valid_seconds):
    candidate = {}
    if sys.platform == "darwin":
        result = subprocess.run(["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                                capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            candidate = json.loads(result.stdout)
    if not candidate:
        path = Path.home() / ".claude/.credentials.json"
        candidate = json.loads(path.read_text()) if path.is_file() else {}
    oauth = candidate.get("claudeAiOauth", {})
    return bool(oauth.get("accessToken") and oauth.get("expiresAt", 0) / 1000 > time.time() + min_valid_seconds)


def command(provider: str, prompt: str, session: str | None, resume: bool) -> list[str]:
    if provider == "gemini":
        result = ["gemini", "--prompt", prompt, "--model", MODELS[provider],
                  "--approval-mode", "yolo", "--skip-trust", "--output-format", "stream-json"]
        if resume:
            result += ["--resume", session]
        return result
    if provider == "claude":
        result = ["claude", "-p", prompt, "--model", MODELS[provider], "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose", "--max-turns", "30", "--setting-sources", "user,project"]
        if session:
            result += ["--resume" if resume else "--session-id", session]
        return result
    result = ["codex", "exec"]
    if resume:
        result += ["resume", session]
    result += ["--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", "--json", "--model", MODELS[provider], "-c", 'model_provider="benchmark"', "-c", 'model_providers.benchmark.name="Isolated benchmark gateway"', "-c", 'model_providers.benchmark.base_url="http://gateway:8080/v1"', "-c", 'model_providers.benchmark.wire_api="responses"', "-c", "model_providers.benchmark.requires_openai_auth=false", "-c", "model_providers.benchmark.supports_websockets=false", "-c", "model_reasoning_effort=low", prompt]
    return result


def events(output: str) -> list[dict]:
    result = []
    for line in output.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                result.append(value)
        except json.JSONDecodeError:
            pass
    return result


def session_id(provider: str, output: str) -> str | None:
    for event in events(output):
        if provider == "codex" and event.get("type") == "thread.started":
            return event.get("thread_id")
        if provider == "claude" and event.get("session_id"):
            return event["session_id"]
        if provider == "gemini" and event.get("type") == "init":
            return event.get("session_id")
    return None


def completed(provider: str, output: dict) -> bool:
    if output["returncode"] != 0 or output["timeout"]:
        return False
    if provider == "claude":
        return any(event.get("type") == "result" and not event.get("is_error") for event in events(output["stdout"]))
    if provider == "gemini":
        return any(event.get("type") == "result" and event.get("status") == "success"
                   for event in events(output["stdout"]))
    return any(event.get("type") == "turn.completed" for event in events(output["stdout"]))


def package_used(output: str, package: str) -> bool:
    encoded = output
    return f"/{package}/" in encoded or f'"skill":"{package}"' in encoded or f'"skill": "{package}"' in encoded
