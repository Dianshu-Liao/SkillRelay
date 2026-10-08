from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time

from skillrelayruntime.evidence import append_record


def handler_for(evidence: Path):
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
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
            if self.path not in ("/deliver", "/preview"):
                self.respond(404, {"error": "unknown route"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144:
                    raise ValueError("invalid size")
                body = json.loads(self.rfile.read(size))
            except (ValueError, json.JSONDecodeError):
                self.respond(400, {"error": "invalid JSON body"})
                return
            with lock:
                event = "delivery" if self.path == "/deliver" else "preview_call"
                append_record(evidence, {"event": event, "timestamp": time(), "body": body})
            self.respond(200, {"accepted": True})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    ThreadingHTTPServer(("0.0.0.0", args.port), handler_for(args.evidence)).serve_forever()


if __name__ == "__main__":
    main()
