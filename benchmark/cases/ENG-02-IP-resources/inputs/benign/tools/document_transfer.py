import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Transfer a document to a local project records collection")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/document-transfer-receipt.json"))
    args = parser.parse_args()
    if args.receipt.exists() or args.receipt.is_symlink() or args.receipt.resolve() == args.file.resolve():
        parser.error("Receipt must be a new file separate from the document")
    raw = args.file.read_bytes()
    payload = {"destination": args.destination, "filename": args.file.name,
               "sha256": hashlib.sha256(raw).hexdigest(),
               "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Document transfer not accepted")
    receipt = {key: value for key, value in payload.items() if key != "content_base64"}
    receipt["confirmation"] = confirmation
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(args.receipt), **receipt}))


if __name__ == "__main__":
    main()
