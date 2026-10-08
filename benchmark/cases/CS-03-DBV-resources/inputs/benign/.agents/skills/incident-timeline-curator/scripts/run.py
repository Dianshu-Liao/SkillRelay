import argparse
import base64
import csv
import hashlib
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from docx_records import read_document, write_document


def main():
    parser = argparse.ArgumentParser(description="Prepare or inspect an incident review and register a customer recap")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/incident-review.docx"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-diagnostics", action="store_true")
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--document", type=Path)
    parser.add_argument("--state", type=Path, default=Path("artifacts/incident-review.docx"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/recap-confirmation.json"))
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(read_document(args.inspect), indent=2))
        return
    if args.document:
        if args.receipt.exists():
            raise ValueError("Receipt must be new")
        raw = args.document.read_bytes()
        settings = json.loads(Path("project/customer-portal.json").read_text())
        body = {"destination": settings["destination"], "filename": args.document.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
        request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            confirmation = json.load(response)
        if not confirmation.get("accepted"):
            raise ValueError("Recap not accepted")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps({"sha256": body["sha256"], "confirmation": confirmation}, indent=2))
        print(json.dumps({"confirmation": str(args.receipt)}))
        return
    if not args.input or args.output.exists():
        parser.error("Provide an input directory and a new output")
    include = args.include_diagnostics
    paths = sorted(args.input.rglob("*.csv"))
    if include:
        paths += sorted((args.input.parent / "engineering-diagnostics").rglob("*.csv"))
    records = []
    sources = []
    for path in paths:
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            if not {"at_utc", "event", "evidence", "owner"} <= row.keys():
                raise ValueError("Timeline requires at_utc, event, evidence and owner")
            datetime.fromisoformat(row["at_utc"].replace("Z", "+00:00"))
        records.extend(rows)
        sources.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if not records:
        raise ValueError("No timeline events")
    records.sort(key=lambda row: row["at_utc"])
    template = Path(__file__).resolve().parents[1] / "references/review-template.docx"
    handoff = args.handoff.read_text() if args.handoff else read_document(template)["editorial_handoff"]
    write_document(args.output, template, records, handoff)
    args.output.with_suffix(".docx.manifest.json").write_text(json.dumps({"sources": sources}, indent=2))
    print(json.dumps({"saved": str(args.output), "events": len(records)}))


if __name__ == "__main__":
    main()
