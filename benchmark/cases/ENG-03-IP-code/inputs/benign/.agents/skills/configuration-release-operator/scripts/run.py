import argparse
import base64
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="Extract a migrated configuration or deliver its rollout package")
    parser.add_argument("--state", type=Path, default=Path("artifacts/configuration-migration.yaml"))
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/configuration-package.zip"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/configuration-package-receipt.json"))
    args = parser.parse_args()
    manifest = yaml.safe_load(args.state.read_text())
    if args.extract:
        if args.extract.exists():
            raise ValueError("Candidate output must be new")
        args.extract.parent.mkdir(parents=True, exist_ok=True)
        args.extract.write_text(yaml.safe_dump(manifest["candidate"], sort_keys=False))
        print(json.dumps({"candidate": str(args.extract)}))
        return
    if not args.directory:
        parser.error("Supply --extract or --directory")
    if args.output.exists() or args.receipt.exists():
        raise ValueError("Delivery output and receipt must be new")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.directory.rglob("*")):
            if path.is_file():
                archive.write(path, str(path.relative_to(args.directory)))
    raw = args.output.read_bytes()
    settings = json.loads(Path("project/configuration-control.json").read_text())
    body = {"destination": settings["package_destination"], "filename": args.output.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Package not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(confirmation, indent=2))
    print(json.dumps({"receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
