import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Inspect an opportunity handoff or register an authored CRM update")
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--state", type=Path, default=Path("artifacts/opportunity-handoff.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/crm-update-receipt.json"))
    args = parser.parse_args()
    if args.inspect:
        print(args.inspect.read_text())
        return
    if not args.request or args.receipt.exists():
        parser.error("Supply request and a new receipt path")
    record = json.loads(args.request.read_text())
    required = {"opportunity_id", "changes", "handoff_note"}
    if not required <= record.keys() or not isinstance(record["changes"], dict):
        parser.error("CRM update requires opportunity_id, changes and handoff_note")
    schema = json.loads(Path("project/crm-schema.json").read_text())
    for field, value in record["changes"].items():
        if field not in schema["writable_fields"]:
            parser.error("Field not writable: " + field)
        if field in schema["picklists"] and value not in schema["picklists"][field]:
            parser.error("Invalid picklist value for " + field)
    raw = args.request.read_bytes()
    settings = json.loads(Path("project/crm-service.json").read_text())
    body = {"destination": settings["destination"], "filename": args.request.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("CRM update not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"update": record, "confirmation": confirmation}, indent=2))
    print(json.dumps({"receipt": str(args.receipt), "accepted": True}))


if __name__ == "__main__":
    main()
