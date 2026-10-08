import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def inspect(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        records = [json.loads(row[0]) for row in database.execute("SELECT payload FROM records")]
        correspondence = [json.loads(row[0]) for row in database.execute("SELECT payload FROM correspondence")]
        handoff = database.execute("SELECT body FROM handoff").fetchone()[0]
    return {"records": records, "correspondence": correspondence, "disposition_handoff": handoff}


def main():
    parser = argparse.ArgumentParser(description="Prepare a records retention workpaper with deadlines and hold evidence")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/retention-review.sqlite3"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-correspondence", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply input and a new output path")
    catalog = args.input / "catalog.json"
    records = json.loads(catalog.read_text())["records"]
    include = args.include_correspondence
    sources = [catalog]
    correspondence = []
    if include:
        for path in sorted((args.input.parent / "employee-correspondence").glob("*.txt")):
            correspondence.append({"filename": path.name, "body": path.read_text()})
            sources.append(path)
    guide = Path(__file__).resolve().parents[1] / "references/retention-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.output) as database:
        database.executescript("CREATE TABLE records(record_id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE correspondence(filename TEXT PRIMARY KEY,payload TEXT);CREATE TABLE handoff(body TEXT);CREATE TABLE sources(path TEXT,sha256 TEXT);")
        database.executemany("INSERT INTO records VALUES (?,?)", [(record["record_id"], json.dumps(record)) for record in records])
        database.executemany("INSERT INTO correspondence VALUES (?,?)", [(record["filename"], json.dumps(record)) for record in correspondence])
        database.execute("INSERT INTO handoff VALUES (?)", (handoff,))
        database.executemany("INSERT INTO sources VALUES (?,?)", [(str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in sources])
    print(json.dumps({"saved": str(args.output), "records": len(records), "correspondence": len(correspondence)}))


if __name__ == "__main__":
    main()
