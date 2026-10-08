import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path

from payables_workbook import read_document


def main():
    parser = argparse.ArgumentParser(description="Inspect invoice workpapers or register an authored payable import")
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--state", type=Path, default=Path("artifacts/invoice-reconciliation.xlsx"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/payables-import-receipt.json"))
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(read_document(args.inspect), indent=2))
        return
    if not args.request or args.receipt.exists():
        parser.error("Supply a request and a new receipt path")
    request_record = json.loads(args.request.read_text())
    if not {"payables", "exceptions", "supporting_references"} <= request_record.keys():
        parser.error("Request needs payables, exceptions and supporting_references")
    for payable in request_record["payables"]:
        if not {"invoice_id", "vendor", "amount", "currency"} <= payable.keys() or payable["amount"] <= 0:
            parser.error("Payable needs identifier, vendor, positive amount and currency")
    raw = args.request.read_bytes()
    settings = json.loads(Path("project/payables-portal.json").read_text())
    body = {"destination": settings["destination"], "filename": args.request.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("accepted"):
        raise ValueError("Payables import not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2))
    print(json.dumps({"receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
