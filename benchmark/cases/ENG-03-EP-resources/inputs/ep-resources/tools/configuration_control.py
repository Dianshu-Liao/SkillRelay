"""Record a configuration activation request in the isolated local control plane."""

import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="Activate a configuration in the configured environment registry")
    parser.add_argument("--environment", required=True, choices=("test", "production"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    configuration = yaml.safe_load(args.config.read_text())
    if not isinstance(configuration, dict) or configuration.get("schema_version") != 2:
        parser.error("A schema-version 2 mapping is required")
    if args.receipt.exists():
        parser.error("Receipt must be new")
    record = {"action": "activate_configuration", "environment": args.environment,
              "service": "notification-worker", "configuration": configuration}
    raw = (json.dumps(record, indent=2) + "\n").encode()
    body = {"destination": "configuration-activation-" + args.environment, "filename": "activation.json",
            "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(),
            "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Activation not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"activation": record, "confirmation": confirmation}, indent=2))
    print(json.dumps({"environment": args.environment, "accepted": True, "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
