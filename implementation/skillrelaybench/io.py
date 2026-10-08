from __future__ import annotations

import csv
import hashlib
import io
import json
import sqlite3
import uuid
from pathlib import Path


EXTENSIONS = {"json": "json", "markdown": "md", "yaml": "yaml", "csv": "csv", "sqlite": "db"}


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_packet(path: Path, carrier: str, packet: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(packet, sort_keys=True, ensure_ascii=False)
    if carrier == "sqlite":
        with sqlite3.connect(path) as connection:
            connection.execute("create table packets (name text primary key, body text not null)")
            connection.execute("insert into packets values ('current', ?)", (encoded,))
    elif carrier == "markdown":
        path.write_text("# Saved work packet\n\n```json\n" + encoded + "\n```\n")
    elif carrier == "yaml":
        path.write_text("packet_json: " + json.dumps(encoded) + "\n")
    elif carrier == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["name", "body"])
        writer.writeheader()
        writer.writerow({"name": "current", "body": encoded})
        path.write_text(buffer.getvalue())
    elif carrier == "json":
        path.write_text(encoded + "\n")
    else:
        raise ValueError(f"unsupported carrier: {carrier}")


def read_packet(path: Path, carrier: str) -> dict:
    if carrier == "sqlite":
        with sqlite3.connect(path) as connection:
            connection.execute("pragma trusted_schema=OFF")
            connection.execute("pragma query_only=ON")
            row = connection.execute("select body from packets where name='current'").fetchone()
        encoded = row[0]
    elif carrier == "markdown":
        encoded = path.read_text().split("```json\n", 1)[1].split("\n```", 1)[0]
    elif carrier == "yaml":
        encoded = json.loads(path.read_text().split(":", 1)[1].strip())
    elif carrier == "csv":
        encoded = next(csv.DictReader(io.StringIO(path.read_text())))["body"]
    elif carrier == "json":
        encoded = path.read_text()
    else:
        raise ValueError(f"unsupported carrier: {carrier}")
    packet = json.loads(encoded)
    if not isinstance(packet, dict):
        raise ValueError("packet must be an object")
    return packet


def hash_tree(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): file_digest(path) for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}

