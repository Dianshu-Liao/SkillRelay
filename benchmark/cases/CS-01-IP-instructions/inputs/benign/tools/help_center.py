import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Store and retrieve articles in a local mock help center")
    parser.add_argument("--store", type=Path, required=True)
    commands = parser.add_subparsers(dest="operation", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("--article", type=Path, required=True)
    publish.add_argument("--title", required=True)
    retrieve = commands.add_parser("get")
    retrieve.add_argument("--id", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "publish":
            body = args.article.read_text(encoding="utf-8")
            if not body.strip() or not args.title.strip():
                raise ValueError("article and title must not be empty")
            args.store.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(args.store) as connection:
                connection.execute("CREATE TABLE IF NOT EXISTS articles (article_id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, sha256 TEXT NOT NULL, published_at TEXT NOT NULL)")
                metadata = {"article_id": uuid.uuid4().hex, "title": args.title, "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "published_at": datetime.now(timezone.utc).isoformat()}
                connection.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?)", (metadata["article_id"], args.title, body, metadata["sha256"], metadata["published_at"]))
            print(json.dumps(metadata))
        else:
            with sqlite3.connect(args.store.resolve().as_uri() + "?mode=ro", uri=True) as connection:
                connection.row_factory = sqlite3.Row
                record = connection.execute("SELECT * FROM articles WHERE article_id = ?", (args.id,)).fetchone()
            if record is None:
                raise ValueError("article not found")
            print(json.dumps(dict(record)))
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Help center: {error}\n")


if __name__ == "__main__":
    main()
