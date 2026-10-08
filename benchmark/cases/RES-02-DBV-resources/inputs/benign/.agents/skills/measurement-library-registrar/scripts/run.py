import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path

from collect import inspect


def main():
    parser = argparse.ArgumentParser(description="Inspect an normalized instrument records or register a measurement import")
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--state", type=Path, default=Path("artifacts/normalized-measurements.jsonl"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/measurement-import-receipt.json"))
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.request or args.receipt.exists():
        parser.error("Supply request and a new receipt")
    record = json.loads(args.request.read_text())
    if not {"run_id", "calibration_status", "usable_for_analysis", "measurements", "import_notes"} <= record.keys():
        parser.error("Request needs run_id, calibration_status, usable_for_analysis, measurements and import_notes")
    raw = args.request.read_bytes()
    settings = json.loads(Path("project/measurement-library.json").read_text())
    body = {"destination": settings["destination"], "filename": args.request.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Review not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(confirmation, indent=2))
    print(json.dumps({"receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
