import argparse
import hashlib
import html
import json
from pathlib import Path


def inspect(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description="Prepare an experiment evidence review and HTML reading copy")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/experiment-review.json"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-events", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists() or args.output.with_suffix(".html").exists():
        parser.error("Supply experiment directory and a new output pair")
    paths = [args.input / "plan.json", args.input / "results.json"]
    plan, results = [json.loads(path.read_text()) for path in paths]
    events = []
    include = True
    if include:
        extra = args.input.parent / "user-events/events.jsonl"
        events = [json.loads(line) for line in extra.read_text().splitlines() if line.strip()]
        paths.append(extra)
    guide = Path(__file__).resolve().parents[1] / "references/experiment-guide.txt"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    review = {"plan": plan, "results": results, "event_appendix": events, "decision_handoff": handoff, "sources": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(review, indent=2))
    rows = "".join("<tr><td>" + html.escape(str(row["arm"])) + "</td><td>" + str(row["enrolled"]) + "</td><td>" + str(row["converted"]) + "</td></tr>" for row in results["arms"])
    document = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Experiment evidence review</title><style>body{font:18px system-ui;max-width:960px;margin:40px auto;padding:24px;color:#203441}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bdcbd2;padding:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f7;padding:16px}</style><h1>Experiment evidence review</h1><h2>Enrollment and conversions</h2><table><tr><th>Arm</th><th>Enrolled</th><th>Converted</th></tr>' + rows + '</table><h2>Decision handoff</h2><pre>' + html.escape(handoff) + '</pre><h2>Plan and supporting evidence</h2><pre>' + html.escape(json.dumps(review, indent=2)) + '</pre></html>'
    args.output.with_suffix(".html").write_text(document)
    print(json.dumps({"saved": str(args.output), "reading_copy": str(args.output.with_suffix(".html")), "event_rows": len(events)}))


if __name__ == "__main__":
    main()
