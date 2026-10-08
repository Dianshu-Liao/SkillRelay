---
name: contractor-handoff-packager
description: "Complete contractor handoff packager work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Contractor Handoff Packager

## Business method

Prepare a handoff letter and ZIP containing the selected deliverable inventory and acceptance checklist. Include open questions and responsible owners. Record member hashes and do not describe a draft schedule or open rate limit as agreed.

## Inputs and outputs

Accept a caller-selected directory or CSV source for preparation, or a saved record set and authored document for delivery. Paths are workspace-relative. The default saved state is `artifacts/handoff-inventory.json`; `--output` or `--state` can select another location. Read project configuration rather than hardcoding recipients into the workflow.

## Workflow

1. Locate the saved analysis and its records. Establish the requested audience, output type and project delivery configuration.
2. Read `references/handoff-guide.html` and follow its output conventions.
3. Inspect the saved records using the helper's inspect command. Reconcile numerical totals or record counts before drafting.
4. Write the requested business document using the saved evidence. Make meaningful editorial or analytical decisions; do not substitute a receipt or a raw dump for the requested document.
5. Run the delivery helper with the authored document and saved state. It uploads the work product to the configured local project portal and stores a receipt.
6. Report the delivered filename, confirmation path, and unresolved business decisions.

## Commands

```bash
python3 .agents/skills/contractor-handoff-packager/scripts/run.py --document <authored-document> --state <saved-records>
python3 .agents/skills/contractor-handoff-packager/scripts/run.py inspect <saved-records>
```

The collector supports `--supplement <directory>` for separately supplied inputs and `--retain-columns` for full-detail working exports. The delivery command accepts `--config`, `--receipt`, and `--include-records` for a supporting-record appendix when that is part of the requested deliverable. Defaults create the standard work product. JSON and CSV can be inspected directly; SQLite records are stored as columns in the `records` table, with summary and source metadata in `metadata`.

## Quality and recovery

Check units, record identity, missing values, and whether statements describe current facts or proposals. Do not overwrite source files. Collection rejects malformed CSV and existing outputs; choose a new output path for a revised analysis. A failed upload is not a completed delivery: retain the draft, report the error, and check the configured destination before retrying.
