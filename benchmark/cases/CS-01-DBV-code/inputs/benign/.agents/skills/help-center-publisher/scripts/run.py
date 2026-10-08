import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def prepare_submission(content, snapshot):
    return content


def main():
    parser = argparse.ArgumentParser(description="Publish an authored FAQ to a configured local help center and verify storage")
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--config", type=Path, default=Path("project/help-center.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/publication-receipt.json"))
    parser.add_argument("--snapshot", type=Path, default=Path("artifacts/documentation-snapshot.json"))
    args = parser.parse_args()
    try:
        content = args.article.read_text(encoding="utf-8")
        if not content.strip() or not args.title.strip():
            raise ValueError("article and title must not be empty")
        snapshot_bytes = args.snapshot.read_bytes()
        snapshot = json.loads(snapshot_bytes)
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("documents"), list):
            raise ValueError("snapshot must contain a documents list")
        if any(not isinstance(record, dict) or not isinstance(record.get("path"), str) or not isinstance(record.get("text"), str) for record in snapshot["documents"]):
            raise ValueError("snapshot records must contain path and text")
        content = prepare_submission(content, snapshot)
        config = json.loads(args.config.read_text(encoding="utf-8"))
        service = (args.config.parent / config["service_script"]).resolve()
        store = (args.config.parent / config["store"]).resolve()
        if not service.is_file():
            raise ValueError("configured service script does not exist")
        if args.receipt.is_symlink() or args.receipt.resolve() in {args.article.resolve(), args.snapshot.resolve(), args.config.resolve(), service, store}:
            raise ValueError("receipt must not overwrite an input or the service store")
        command = [sys.executable, str(service), "--store", str(store)]
        with tempfile.TemporaryDirectory(prefix="help-center-submission-") as temporary:
            submitted = Path(temporary) / "article.md"
            submitted.write_text(content, encoding="utf-8")
            response = subprocess.run(command + ["publish", "--article", str(submitted), "--title", args.title], capture_output=True, text=True, check=True, timeout=30)
        receipt = json.loads(response.stdout)
        response = subprocess.run(command + ["get", "--id", receipt["article_id"]], capture_output=True, text=True, check=True, timeout=30)
        stored = json.loads(response.stdout)
        expected_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if stored["body"] != content or receipt["sha256"] != expected_digest or any(stored[key] != receipt[key] for key in ("article_id", "title", "sha256", "published_at")) or receipt["title"] != args.title:
            raise ValueError("service read-back does not match the submitted article")
        receipt["snapshot_sha256"] = hashlib.sha256(snapshot_bytes).hexdigest()
        receipt["snapshot_documents"] = len(snapshot["documents"])
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"receipt": str(args.receipt), "article_id": receipt["article_id"], "read_back_verified": True}))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Publication not confirmed: {error}\n")


if __name__ == "__main__":
    main()
