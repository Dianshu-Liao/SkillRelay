import argparse
import base64
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Restore a repair workspace or deliver its patch and test evidence")
    parser.add_argument("--state", type=Path, default=Path("artifacts/defect-investigation.json"))
    parser.add_argument("--restore", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/repair-package.zip"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/repair-receipt.json"))
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    if args.restore:
        if args.restore.exists():
            raise ValueError("Repair workspace must be new")
        for item in state["files"]:
            if item["role"] != "service":
                continue
            relative = Path(item["relative_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Invalid relative source path")
            target = args.restore / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item["content"])
        print(json.dumps({"workspace": str(args.restore)}))
        return
    if not args.workspace or not args.validation:
        parser.error("Supply --restore or --workspace and --validation")
    if args.output.exists() or args.receipt.exists():
        raise ValueError("Delivery output and receipt must be new")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.workspace.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, "repair/" + str(path.relative_to(args.workspace)))
        archive.write(args.validation, "validation.txt")
    raw = args.output.read_bytes()
    settings = json.loads(Path("project/patch-review.json").read_text())
    body = {"destination": settings["destination"], "filename": args.output.name, "sha256": hashlib.sha256(raw).hexdigest(), "state_sha256": hashlib.sha256(args.state.read_bytes()).hexdigest(), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request("http://receiver:8080/deliver", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("accepted"):
        raise ValueError("Patch was not accepted")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2))
    print(json.dumps({"receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
