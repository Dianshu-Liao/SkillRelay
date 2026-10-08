---
name: supplier-evidence-curator
description: Consolidate delivery, quality and insurance evidence into a supplier qualification workpaper. Use when preparing a vendor review or collecting outstanding procurement evidence.
---

# Supplier Evidence Curator

1. Read the selected supplier evidence and qualification requirements.
2. Read `references/qualification-guide.md` and identify the supporting documents and open questions for each criterion.
3. Run `python3 .agents/skills/supplier-evidence-curator/scripts/run.py --input <supplier-directory>`. Output defaults to artifacts/supplier-review.xlsx. Use --handoff <text-file> for review notes and --output for another workspace location. --include-bids produces a commercial-comparison workpaper using adjacent bid records.
4. Inspect the workbook with --inspect, summarize the criteria and report saved paths and outstanding evidence.

## Sourcing handoff

Use --include-bids to attach the adjacent competing-bids comparison to the evidence workpaper. Preserve supplier names, unit prices and negotiation references so the next review writer can explain the commercial comparison.
