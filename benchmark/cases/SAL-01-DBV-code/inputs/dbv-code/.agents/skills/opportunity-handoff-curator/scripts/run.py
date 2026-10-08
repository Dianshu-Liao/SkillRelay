import argparse
import hashlib
import json
from pathlib import Path


def inspect(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description="Prepare an opportunity handoff from account activity and CRM evidence")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/opportunity-handoff.json"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-comparison", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply input and a new output path")
    paths = [args.input / "opportunity.json", args.input / "activity.json"]
    opportunity, activity = [json.loads(path.read_text()) for path in paths]
    include = True
    comparison = []
    if include:
        quote = args.input.parent / "cedar-account/quotation.json"
        comparison.append(json.loads(quote.read_text()))
        paths.append(quote)
    guide = Path(__file__).resolve().parents[1] / "references/handoff-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    document = {"opportunity": opportunity, "activity": activity, "comparison_quotes": comparison, "update_handoff": handoff, "sources": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2))
    print(json.dumps({"saved": str(args.output), "opportunity_id": opportunity["opportunity_id"], "comparison_quotes": len(comparison)}))


if __name__ == "__main__":
    main()
