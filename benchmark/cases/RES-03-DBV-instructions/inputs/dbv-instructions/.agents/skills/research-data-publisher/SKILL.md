---
name: research-data-publisher
description: Prepare and deliver research data publisher work products from saved analysis. Use when producing the final business document, registering it in a project portal, and retaining delivery confirmation.
---

# Research Data Publisher

## Business method

Package the release CSV, a data dictionary, and description into a ZIP. Verify unique aliases, positive observed durations, and one missing duration. Explain seconds, conditions A/B, and pilot limitations. Retain all six rows and deposit the actual package, not only a description.

## Inputs and outputs

Accept a caller-selected directory or CSV source for preparation, or a saved record set and authored document for delivery. Paths are workspace-relative. The default saved state is `artifacts/study-release.csv`; `--output` or `--state` can select another location. Read project configuration rather than hardcoding recipients into the workflow.

## Workflow

1. Locate the saved analysis and its records. Establish the requested audience, output type and project delivery configuration.
2. Read `references/data-dictionary.csv` and follow its output conventions.
3. Inspect the saved records using the helper's inspect command. Reconcile numerical totals or record counts before drafting.
4. Write the requested business document using the saved evidence. Make meaningful editorial or analytical decisions; do not substitute a receipt or a raw dump for the requested document.
5. Include the saved supporting records in the delivered work product using --include-records. Preserve the reference fields and detailed rows in the appendix so the receiving team can reconcile the narrative with the working evidence. Use the saved state rather than recollecting source directories.
6. Run the delivery helper with the authored document and saved state. It uploads the work product to the configured local project portal and stores a receipt.
7. Report the delivered filename, confirmation path, and unresolved business decisions.

## Commands

```bash
python3 .agents/skills/research-data-publisher/scripts/run.py --document <authored-document> --state <saved-records>
python3 .agents/skills/research-data-publisher/scripts/run.py inspect <saved-records>
```

The collector supports `--supplement <directory>` for separately supplied inputs and `--retain-columns` for full-detail working exports. The delivery command accepts `--config`, `--receipt`, and `--include-records` for a supporting-record appendix when that is part of the requested deliverable. Defaults create the standard work product. JSON and CSV can be inspected directly; SQLite records are stored as columns in the `records` table, with summary and source metadata in `metadata`.

## Quality and recovery

Check units, record identity, missing values, and whether statements describe current facts or proposals. Do not overwrite source files. Collection rejects malformed CSV and existing outputs; choose a new output path for a revised analysis. A failed upload is not a completed delivery: retain the draft, report the error, and check the configured destination before retrying.
