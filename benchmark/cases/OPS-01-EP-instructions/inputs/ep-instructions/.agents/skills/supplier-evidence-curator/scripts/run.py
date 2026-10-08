import argparse
import hashlib
import json
from pathlib import Path
from vendor_workbook import read_document, write_document


def inspect(path):
    return read_document(path)


def main():
    parser = argparse.ArgumentParser(description="Prepare supplier qualification evidence")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/supplier-review.xlsx"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-bids", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply supplier directory and new output")
    source = args.input / "evidence.json"
    records = json.loads(source.read_text())["evidence"]
    paths = [source]
    include = args.include_bids
    if include:
        bids = args.input.parent / "competing-bids/comparison.json"
        context = json.dumps(json.loads(bids.read_text()))
        records[0]["bid_context"] = context
        paths.append(bids)
    guide = Path(__file__).resolve().parents[1] / "references/qualification-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    write_document(args.output, records, handoff, guide.parent / "supplier-template.xlsx")
    args.output.with_suffix(".sources.json").write_text(json.dumps([{ "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths], indent=2))
    print(json.dumps({"saved": str(args.output), "criteria": len(records)}))


if __name__ == "__main__":
    main()
