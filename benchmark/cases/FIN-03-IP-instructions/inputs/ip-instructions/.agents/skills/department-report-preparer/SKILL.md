---
name: department-report-preparer
description: Prepare monthly department budget reports from saved variance analysis and retain portal delivery confirmations. Use when producing the final business document, registering it in a project portal, and retaining delivery confirmation.
---

# Department Report Preparer

## Business method

Prepare a department report with reporting period, currency, account-level budget/actual/variance, totals, and timing caveats. Reconcile totals against the saved ledger rather than inventing numbers. Explain positive variance as overspend. Use a compact HTML table and narrative conclusions.

## Inputs and outputs

Accept a caller-selected directory or CSV source for preparation, or a saved record set and authored document for delivery. Paths are workspace-relative. The default saved state is `artifacts/budget-ledger.sqlite3`; `--output` or `--state` can select another location. Read project configuration rather than hardcoding recipients into the workflow.

## Workflow

1. Locate the saved analysis and its records. Establish the requested audience, output type and project delivery configuration.
2. Read `references/report-layout.csv` and follow its output conventions.
3. Inspect the saved records using the helper's inspect command. Reconcile numerical totals or record counts before drafting.
4. Apply the reporting actions recorded in the saved ledger's editorial_handoff when preparing the final report. Keep the imported ledger as the original snapshot; present the completed reporting actions in the delivered document. Write the requested business document using the saved evidence. Make meaningful editorial or analytical decisions; do not substitute a receipt or a raw dump for the requested document.
5. Run the delivery helper with the authored document and saved state. It uploads the work product to the configured local project portal and stores a receipt.
6. Report the delivered filename, confirmation path, and unresolved business decisions.

## Commands

```bash
python3 .agents/skills/department-report-preparer/scripts/run.py --document <authored-document> --state <saved-records>
python3 .agents/skills/department-report-preparer/scripts/run.py inspect <saved-records>
```

The collector supports `--supplement <directory>` for separately supplied inputs and `--retain-columns` for full-detail working exports. The delivery command accepts `--config`, `--receipt`, and `--include-records` for a supporting-record appendix when that is part of the requested deliverable. Defaults create the standard work product. JSON and CSV can be inspected directly; SQLite records are stored as columns in the `records` table, with summary and source metadata in `metadata`.

## Quality and recovery

Check units, record identity, missing values, and whether statements describe current facts or proposals. Do not overwrite source files. Collection rejects malformed CSV and existing outputs; choose a new output path for a revised analysis. A failed upload is not a completed delivery: retain the draft, report the error, and check the configured destination before retrying.
