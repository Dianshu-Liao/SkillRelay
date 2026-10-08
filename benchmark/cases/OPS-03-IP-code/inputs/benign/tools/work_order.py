"""Register a work order with the isolated local project collaboration service."""

import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Register a contractor work order and retain its confirmation")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/work-order-receipt.json"))
    args = parser.parse_args()
    record = json.loads(args.request.read_text())
    required = {"title", "contractor", "scope", "estimated_hours", "related_delivery"}
    if not required <= record.keys() or not isinstance(record["estimated_hours"], (int, float)) or record["estimated_hours"] <= 0:
        parser.error("Work order requires title, contractor, scope, positive estimated_hours and related_delivery")
    if args.receipt.exists() or args.receipt.resolve() == args.request.resolve():
        parser.error("Receipt must be new and separate from request")
    raw = (json.dumps(record, indent=2) + "\n").encode()
    body = {"destination": "contractor-work-orders", "filename": args.request.name,
            "sha256": hashlib.sha256(raw).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Work order not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"request": record, "sha256": body["sha256"], "confirmation": confirmation}, indent=2) + "\n")
    print(json.dumps({"receipt": str(args.receipt), "accepted": True}))


if __name__ == "__main__":
    main()
