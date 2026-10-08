import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def inspect(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return {"studies": [json.loads(row[0]) for row in database.execute("SELECT payload FROM studies ORDER BY study_id")], "lab_notes": [json.loads(row[0]) for row in database.execute("SELECT payload FROM lab_notes")], "editorial_handoff": database.execute("SELECT body FROM handoff").fetchone()[0]}


def main():
    parser = argparse.ArgumentParser(description="Extract study evidence into a synthesis workpaper")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/literature-evidence.sqlite3"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-lab-notes", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply study directory and a new output")
    source = args.input / "studies.json"
    studies = json.loads(source.read_text())["studies"]
    paths = [source]
    lab_notes = []
    include = args.include_lab_notes
    if include:
        extra = args.input.parent / "lab-notes/pilot.json"
        lab_notes = [json.loads(extra.read_text())]
        paths.append(extra)
    guide = Path(__file__).resolve().parents[1] / "references/synthesis-guide.txt"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.output) as database:
        database.executescript("CREATE TABLE studies(study_id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE lab_notes(payload TEXT);CREATE TABLE handoff(body TEXT);CREATE TABLE sources(path TEXT,sha256 TEXT);")
        database.executemany("INSERT INTO studies VALUES (?,?)", [(row["study_id"], json.dumps(row)) for row in studies])
        database.executemany("INSERT INTO lab_notes VALUES (?)", [(json.dumps(row),) for row in lab_notes])
        database.execute("INSERT INTO handoff VALUES (?)", (handoff,))
        database.executemany("INSERT INTO sources VALUES (?,?)", [(str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths])
    print(json.dumps({"saved": str(args.output), "studies": len(studies), "lab_notes": len(lab_notes)}))


if __name__ == "__main__":
    main()
