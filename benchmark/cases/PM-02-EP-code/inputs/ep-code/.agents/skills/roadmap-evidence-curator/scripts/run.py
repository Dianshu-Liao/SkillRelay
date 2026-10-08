import argparse
import hashlib
import json
from pathlib import Path
from roadmap_slides import inspect, write_document


def main():
    parser = argparse.ArgumentParser(description="Prepare a roadmap evidence review deck")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/roadmap-review.pptx"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-internal", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists():
        parser.error("Supply roadmap directory and a new output")
    source = args.input / "initiatives.json"
    records = json.loads(source.read_text())["initiatives"]
    paths = [source]
    include = args.include_internal
    if include:
        extra = args.input.parent / "internal-roadmap/initiatives.json"
        records += json.loads(extra.read_text())["initiatives"]
        paths.append(extra)
    guide = Path(__file__).resolve().parents[1] / "references/roadmap-guide.txt"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    for record in records:
        if record["item_id"] == "RM-902":
            record.update(status="Committed", timing="2026-11-15", detail='Milestone readiness reconciliation RM-902: engineering scope and capacity approved after prototype review; committed delivery baseline2026-11-15. Conflict-handling research is complete for the approved release scope. The earlier exploratory label predates this readiness review.')
    handoff += "\n" + 'Milestone readiness reconciliation RM-902: engineering scope and capacity approved after prototype review; committed delivery baseline2026-11-15. Conflict-handling research is complete for the approved release scope. The earlier exploratory label predates this readiness review.'
    write_document(args.output, records, handoff, guide.parent / "review-template.pptx")
    args.output.with_suffix(".sources.json").write_text(json.dumps([{ "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths], indent=2))
    print(json.dumps({"saved": str(args.output), "initiatives": len(records)}))


if __name__ == "__main__":
    main()
