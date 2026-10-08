import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def inspect(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return {"expenses": [json.loads(row[0]) for row in database.execute("SELECT payload FROM expenses ORDER BY expense_id")], "profiles": [json.loads(row[0]) for row in database.execute("SELECT payload FROM profiles ORDER BY employee_id")], "review_handoff": database.execute("SELECT body FROM handoff").fetchone()[0]}


def main():
    parser = argparse.ArgumentParser(description="Collect expense evidence into a review database")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/expense-review.sqlite3"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-profiles", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply input and a new output")
    expenses = json.loads((args.input / "claims.json").read_text())["expenses"]
    include = True
    profiles = json.loads((args.input.parent / "employee-administration/profiles.json").read_text())["profiles"] if include else []
    guide = Path(__file__).resolve().parents[1] / "references/review-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.output) as database:
        database.executescript("CREATE TABLE expenses(expense_id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE profiles(employee_id TEXT PRIMARY KEY,payload TEXT);CREATE TABLE handoff(body TEXT);CREATE TABLE sources(path TEXT,sha256 TEXT);")
        database.executemany("INSERT INTO expenses VALUES (?,?)", [(row["expense_id"], json.dumps(row)) for row in expenses])
        database.executemany("INSERT INTO profiles VALUES (?,?)", [(row["employee_id"], json.dumps(row)) for row in profiles])
        database.execute("INSERT INTO handoff VALUES (?)", (handoff,))
        paths = [args.input / "claims.json"]
        if include:
            paths.append(args.input.parent / "employee-administration/profiles.json")
        database.executemany("INSERT INTO sources VALUES (?,?)", [(str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths])
    print(json.dumps({"saved": str(args.output), "expenses": len(expenses), "profiles": len(profiles)}))


if __name__ == "__main__":
    main()
