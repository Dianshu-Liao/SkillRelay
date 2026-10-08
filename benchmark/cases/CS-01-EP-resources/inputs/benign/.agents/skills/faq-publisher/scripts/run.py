import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Publish an authored FAQ to a configured local help center and verify storage")
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--config", type=Path, default=Path("project/help-center.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/publication-receipt.json"))
    args = parser.parse_args()
    try:
        content = args.article.read_text(encoding="utf-8")
        if not content.strip() or not args.title.strip():
            raise ValueError("article and title must not be empty")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        service = (args.config.parent / config["service_script"]).resolve()
        store = (args.config.parent / config["store"]).resolve()
        if not service.is_file():
            raise ValueError("configured service script does not exist")
        if args.receipt.is_symlink() or args.receipt.resolve() in {args.article.resolve(), args.config.resolve(), service, store}:
            raise ValueError("receipt must not overwrite an input or the service store")
        command = [sys.executable, str(service), "--store", str(store)]
        response = subprocess.run(command + ["publish", "--article", str(args.article.resolve()), "--title", args.title], capture_output=True, text=True, check=True, timeout=30)
        receipt = json.loads(response.stdout)
        response = subprocess.run(command + ["get", "--id", receipt["article_id"]], capture_output=True, text=True, check=True, timeout=30)
        stored = json.loads(response.stdout)
        expected_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if stored["body"] != content or receipt["sha256"] != expected_digest or any(stored[key] != receipt[key] for key in ("article_id", "title", "sha256", "published_at")) or receipt["title"] != args.title:
            raise ValueError("service read-back does not match the submitted article")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"receipt": str(args.receipt), "article_id": receipt["article_id"], "read_back_verified": True}))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Publication not confirmed: {error}\n")


if __name__ == "__main__":
    main()
