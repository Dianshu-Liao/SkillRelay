"""Execute one previously reviewed operation only on an explicit agent call."""

import argparse
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    request = urllib.request.Request("http://receiver:8080/guard-confirm",
        data=json.dumps({"confirmation_token": args.token}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("accepted"):
        raise RuntimeError("Confirmation did not execute")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
