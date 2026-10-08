import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def inspect(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return {"stock": [json.loads(row[0]) for row in database.execute("SELECT payload FROM stock")], "customer_demand": [json.loads(row[0]) for row in database.execute("SELECT payload FROM demand")], "replenishment_handoff": database.execute("SELECT body FROM handoff").fetchone()[0]}


def main():
    parser = argparse.ArgumentParser(description="Reconcile stock and inbound evidence for replenishment")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/stock-review.sqlite3"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-demand", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply inventory directory and new output")
    source = args.input / "stock.json"
    stock = json.loads(source.read_text())["stock"]
    paths = [source]
    demand = []
    include = args.include_demand
    if include:
        extra = args.input.parent / "customer-demand/orders.json"
        demand = json.loads(extra.read_text())["orders"]
        paths.append(extra)
    guide = Path(__file__).resolve().parents[1] / "references/replenishment-guide.txt"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.output) as database:
        database.executescript("CREATE TABLE stock(sku TEXT PRIMARY KEY,payload TEXT);CREATE TABLE demand(payload TEXT);CREATE TABLE handoff(body TEXT);CREATE TABLE sources(path TEXT,sha256 TEXT);")
        database.executemany("INSERT INTO stock VALUES (?,?)", [(row["sku"], json.dumps(row)) for row in stock])
        database.executemany("INSERT INTO demand VALUES (?)", [(json.dumps(row),) for row in demand])
        database.execute("INSERT INTO handoff VALUES (?)", (handoff,))
        database.executemany("INSERT INTO sources VALUES (?,?)", [(str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths])
    print(json.dumps({"saved": str(args.output), "items": len(stock)}))


if __name__ == "__main__":
    main()
