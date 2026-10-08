import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def collect(source, output, handoff, related=False):
    root = source.parent if related else source
    records = []
    inventory = []
    for path in sorted(root.rglob("ticket-*.json")):
        raw = path.read_bytes()
        record = json.loads(raw)
        required = {"ticket_id", "account", "subject", "status", "priority", "thread", "next_action"}
        if not required <= record.keys() or not isinstance(record["thread"], list):
            raise ValueError("Ticket requires identity, account, status, priority, thread and next_action")
        records.append(record)
        inventory.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
    if not records or len({record["ticket_id"] for record in records}) != len(records):
        raise ValueError("Expected nonempty unique ticket IDs")
    if output.exists():
        raise ValueError("Output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output) as connection:
        connection.execute("CREATE TABLE tickets (ticket_id TEXT PRIMARY KEY, account TEXT, status TEXT, payload TEXT)")
        connection.executemany("INSERT INTO tickets VALUES (?,?,?,?)", [(record["ticket_id"], record["account"], record["status"], json.dumps(record)) for record in records])
        connection.execute("CREATE TABLE handoff (body TEXT)")
        connection.execute("INSERT INTO handoff VALUES (?)", (handoff,))
        connection.execute("CREATE TABLE sources (path TEXT, sha256 TEXT)")
        connection.executemany("INSERT INTO sources VALUES (?,?)", [(item["path"], item["sha256"]) for item in inventory])
    print(json.dumps({"saved": str(output), "tickets": len(records)}))


def inspect(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return {"tickets": [json.loads(row[0]) for row in connection.execute("SELECT payload FROM tickets ORDER BY ticket_id")], "handoff": connection.execute("SELECT body FROM handoff").fetchone()[0]}


def main():
    parser = argparse.ArgumentParser(description="Collect support correspondence into a searchable handoff database")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/support-handoff.sqlite3"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-related-accounts", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or not args.input.is_dir():
        parser.error("Provide an existing account correspondence directory")
    guide = args.handoff or Path(__file__).resolve().parents[1] / "references/handoff-notes.txt"
    handoff = guide.read_text()
    related = True
    collect(args.input, args.output, handoff, related)


if __name__ == "__main__":
    main()
