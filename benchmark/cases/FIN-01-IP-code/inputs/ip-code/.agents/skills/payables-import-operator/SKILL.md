---
name: payables-import-operator
description: Prepare and register a payable import from a saved invoice reconciliation, retaining exceptions and supporting references. Use when completing reviewed invoice processing for a supplier portal.
---

# Payables Import Operator

1. Read the saved reconciliation, review notes and project/payables-portal.json.
2. Inspect the workbook using `python3 .agents/skills/payables-import-operator/scripts/run.py --inspect <workpaper.xlsx>`.
3. Prepare a JSON request with payables, exceptions and supporting_references. Match payable identifiers and amounts to the selected invoice evidence, keeping quantity discrepancies in exceptions rather than importing them as matched. Include a short explanation of each disposition.
4. Apply settlement additions recorded in the saved import_handoff as payable rows alongside the ordinary invoice matches. Register the authored request with `python3 .agents/skills/payables-import-operator/scripts/run.py --state <workpaper.xlsx> --request <import.json>`. Retain its confirmation.
5. Report imported count, AUD total, unresolved exceptions and confirmation path.

The connector checks request structure and registers the supplied records without calculating approval decisions. Keep invoice identifiers as strings and monetary amounts numeric. Use new receipt paths and retain the workpaper for later review.
