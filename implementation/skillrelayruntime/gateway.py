from __future__ import annotations

import argparse
import fcntl
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time

GLOBAL_REQUEST_LIMIT = 400000

from skillrelayruntime.evidence import append_record, read_records


class Limits:
    def __init__(self, path: Path, requests: int):
        self.path = path
        self.maximum = requests
        self.count = sum(record.get("event") == "request_reserved" for record in read_records(path))
        self.lock = threading.Lock()

    def reserve(self, provider: str, model: str) -> bool:
        with self.lock:
            if self.count >= self.maximum:
                return False
            append_record(self.path, {"event": "request_reserved", "provider": provider, "model": model, "timestamp": time()})
            self.count += 1
            return True


def reserve_global(path: Path, maximum: int = GLOBAL_REQUEST_LIMIT) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        records = [json.loads(line) for line in stream if line.strip()]
        if len(records) >= maximum:
            return False
        stream.write(json.dumps({"timestamp": time(), "event": "codex_request_reserved",
                                 "accounting": "request_count_only"}) + "\n")
        stream.flush()
        return True


def validate_request(provider: str, path: str, body: dict, model: str) -> None:
    if provider == "claude":
        if path.split("?", 1)[0] != "/v1/messages":
            raise ValueError("route not allowed")
        if body.get("model") != model:
            raise ValueError(f"only the configured model {model} is allowed")
    elif provider == "codex":
        if path != "/v1/responses" or body.get("model") != model:
            raise ValueError(f"only configured model {model} Responses requests are allowed")
    else:
        raise ValueError("unknown provider")


def credential_headers(provider: str) -> dict:
    path = Path("/credentials/api-key.json")
    if path.is_file():
        key = json.loads(path.read_text())
        if not isinstance(key, str) or not key:
            raise ValueError("Gateway API key must be a nonempty string")
        return {"x-api-key": key} if provider == "claude" else {"Authorization": "Bearer " + key}
    if provider == "claude":
        credentials = json.loads(Path("/credentials/claude.json").read_text())
        return {"Authorization": "Bearer " + credentials["claudeAiOauth"]["accessToken"]}
    return {}


def handler_for(provider: str, limits: Limits, upstream: str, model: str, max_request_bytes: int = 262144):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *_args):
            pass

        def respond(self, status: int, body: dict):
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            self.respond(200 if self.path == "/health" else 404, {"ready": self.path == "/health"})

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= max_request_bytes:
                    raise ValueError("request exceeds size limit")
                if self.headers.get("Content-Encoding", "identity") != "identity":
                    raise ValueError("compressed requests are not accepted")
                payload = self.rfile.read(size)
                body = json.loads(payload)
                if not isinstance(body, dict):
                    raise ValueError("request must be a JSON object")
                validate_request(provider, self.path, body, model)
                if not limits.reserve(provider, body["model"]):
                    append_record(limits.path, {"event": "local_request_budget_exhausted", "timestamp": time()})
                    self.respond(400, {"error": {"type": "invalid_request_error", "message": "benchmark request budget exhausted"}})
                    return
                if provider == "codex" and not reserve_global(Path("/budget/codex-requests.jsonl")):
                    append_record(limits.path, {"event": "local_request_budget_exhausted", "timestamp": time()})
                    self.respond(400, {"error": {"type": "invalid_request_error", "message": "global request or conservative USD reservation limit exhausted"}})
                    return
                headers = {"Content-Type": "application/json", "Accept": "text/event-stream",
                           **credential_headers(provider)}
                if provider == "claude":
                    for name in ("anthropic-version", "anthropic-beta", "user-agent", "x-app"):
                        if self.headers.get(name):
                            headers[name] = self.headers[name]
                    beta = headers.get("anthropic-beta", "")
                    if "Authorization" in headers and "oauth-2025-04-20" not in beta:
                        headers["anthropic-beta"] = ",".join(filter(None, [beta, "oauth-2025-04-20"]))
                    headers.setdefault("anthropic-version", "2023-06-01")
                    body["max_tokens"] = min(int(body.get("max_tokens") or 4096), 4096)
                else:
                    body["max_output_tokens"] = min(int(body.get("max_output_tokens") or 4096), 4096)
                payload = json.dumps(body).encode()
                request = urllib.request.Request(upstream.rstrip("/") + self.path, data=payload, headers=headers)
                try:
                    response = urllib.request.urlopen(request, timeout=180)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    self.send_response(response.status)
                    self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                    self.end_headers()
                    while chunk := response.read1(8192):
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    append_record(limits.path, {"event": "response_finished", "status": response.status, "timestamp": time()})
            except (ValueError, KeyError) as error:
                self.respond(400, {"error": str(error)})
            except (OSError, urllib.error.URLError):
                append_record(limits.path, {"event": "transport_failure", "timestamp": time()})
                self.close_connection = True
            except TypeError:
                self.respond(400, {"error": "invalid request field type"})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["claude", "codex"], required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--max-requests", type=int, default=12)
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-request-bytes", type=int, default=262144)
    args = parser.parse_args()
    upstream = (os.environ.get("SKILLRELAY_ANTHROPIC_URL", "https://api.anthropic.com") if args.provider == "claude"
                else os.environ.get("SKILLRELAY_RESPONSES_URL", "https://api.openai.com"))
    limits = Limits(args.ledger, args.max_requests)
    ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(args.provider, limits, upstream, args.model, args.max_request_bytes)).serve_forever()


if __name__ == "__main__":
    main()
