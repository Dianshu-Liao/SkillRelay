import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path

from tickets import inspect


def main():
    parser = argparse.ArgumentParser(description="Register a customer handoff and explicit ticket status updates")
    parser.add_argument("--state", type=Path, default=Path("artifacts/support-handoff.sqlite3"))
    parser.add_argument("--document", type=Path)
    parser.add_argument("--updates", type=Path)
    parser.add_argument("--config", type=Path, default=Path("project/support-desk.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/handoff-confirmation.json"))
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.document or not args.updates:
        parser.error("Provide authored handoff document and status-update JSON")
    updates = json.loads(args.updates.read_text())
    if not isinstance(updates, list) or not updates:
        raise ValueError("Expected a nonempty update list")
    for update in updates:
        if not {"ticket_id", "status", "resolution", "next_action"} <= update.keys() or update["status"] not in {"open", "pending_customer", "resolved"}:
            raise ValueError("Each update requires ticket_id, supported status, resolution and next_action")
    if args.receipt.exists():
        raise ValueError("Receipt must be new")
    settings = json.loads(args.config.read_text())
    packet = {"account": settings["account"], "handoff_markdown": args.document.read_text(), "updates": updates}
    raw = (json.dumps(packet, indent=2) + "\n").encode()
    body = {"destination": settings["destination"], "filename": "support-handoff-registration.json", "content_base64": base64.b64encode(raw).decode(), "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Registration rejected")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"account": packet["account"], "updates": updates, "sha256": body["sha256"], "confirmation": confirmation}, indent=2) + "\n")
    print(json.dumps({"confirmation": str(args.receipt), "registered_updates": len(updates)}))


if __name__ == "__main__":
    main()
