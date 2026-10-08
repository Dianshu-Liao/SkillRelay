"""Check local execution prerequisites without calling a model."""

import argparse
import json
import os
import shutil
import subprocess
from urllib.parse import urlparse


def check_runtime(image, agent, guarded=False):
    if not shutil.which("docker"):
        raise RuntimeError("Docker is required for live experiments. Case validation and batch dry runs do not require Docker.")
    for command, description in (
        (["docker", "info", "--format", "{{.ServerVersion}}"], "Docker daemon"),
        (["docker", "image", "inspect", image, "--format", "{{.Id}}"], f"container image {image}"),
    ):
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(f"Unavailable {description}: {result.stderr.strip()}")
    settings = {}
    if agent == "codex":
        settings["SKILLRELAY_RESPONSES_URL"] = "https://api.openai.com"
    elif agent == "gemini":
        if not os.environ.get("SKILLRELAY_CHAT_URL"):
            raise ValueError("Gemini requires SKILLRELAY_CHAT_URL pointing to a Chat Completions-compatible service serving the selected Gemini model")
        settings["SKILLRELAY_CHAT_URL"] = os.environ["SKILLRELAY_CHAT_URL"]
    elif agent == "claude":
        settings["SKILLRELAY_ANTHROPIC_URL"] = "https://api.anthropic.com"
    if guarded:
        settings["SKILLRELAYGUARD_UPSTREAM"] = "https://api.openai.com"
    for name, default in settings.items():
        value = os.environ.get(name, default)
        parsed = urlparse(value)
        if (parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.path.endswith("/v1")):
            raise ValueError(f"{name} must be an HTTP(S) API root without /v1, credentials, query or fragment")
    return {"docker": "available", "image": image, "agent": agent, "guarded": guarded,
            "provider_connectivity": "not tested; no model request or credential lookup performed",
            "required_endpoints": {name: os.environ.get(name, default) for name, default in settings.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="skillrelay:1.0")
    parser.add_argument("--agent", choices=("codex", "gemini", "claude"), default="codex")
    parser.add_argument("--guarded", action="store_true")
    args = parser.parse_args()
    print(json.dumps(check_runtime(args.image, args.agent, args.guarded), indent=2))
