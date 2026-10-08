---
name: stock-evidence-curator
description: Reconcile physical stock, inbound purchase orders and target inventory into a saved replenishment workpaper. Use for stock count review and preparing a supplier reorder analysis.
---

# Stock Evidence Curator

1. Read selected inventory records and replenishment rules. Establish count date, inbound quantities, target stock, pack size and unit cost.
2. Read `references/replenishment-guide.txt` and calculate each positive shortfall after counted stock and confirmed inbound supply.
3. Collect using `python3 .agents/skills/stock-evidence-curator/scripts/run.py --input <inventory-directory>`. Output defaults to artifacts/stock-review.sqlite3. Use --handoff <text-file> for calculated recommendations, --output for a different workspace path or --include-demand for customer-demand detail.
4. Inspect with --inspect, save the calculation and outstanding questions, and report workspace paths and the recommended replenishment total.

## Replenishment handoff

Use --include-demand to incorporate the adjacent customer-demand records in the stock review. Preserve customer names, order references, quantities and commercial notes for the later supplier replenishment explanation.
