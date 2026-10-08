---
name: renewal-account-curator
description: "Prepare and save entitlement history evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Renewal Account Curator

## Business method

Reconcile current and proposed seats, fee, storage, support, and training. Distinguish observed usage from future requirements. Identify missing decisions rather than inventing concessions. Preserve annual currency and tax basis. Save a structured account snapshot for proposal preparation.

## Inputs and outputs

Accept a caller-selected directory or CSV source for preparation, or a saved record set and authored document for delivery. Paths are workspace-relative. The default saved state is `artifacts/account-snapshot.sqlite3`; `--output` or `--state` can select another location. Read project configuration rather than hardcoding recipients into the workflow.

## Workflow

1. Identify the requested business scope, reporting period, units and source directory. Read the project context for field meanings and deliverable requirements.
2. Read `references/proposal-fields.csv` before choosing the output structure. Apply its preparation conventions to this task.
3. Inspect source headers and records, identify missing values, and distinguish measured values from proposed actions.
4. Run the collection helper with the selected source. It validates rows, performs the supported calculations, and saves records with an inventory of source hashes.
5. Read the saved records and calculated summary. Write a short analysis explaining conclusions, limitations and unresolved questions alongside the state.
6. Report the saved analysis and state paths, record count, and any incomplete inputs.

## Commands

```bash
python3 .agents/skills/renewal-account-curator/scripts/run.py --source <selected-directory>
python3 .agents/skills/renewal-account-curator/scripts/run.py inspect <saved-records>
```

The collector supports `--supplement <directory>` for separately supplied inputs and `--retain-columns` for full-detail working exports. The delivery command accepts `--config`, `--receipt`, and `--include-records` for a supporting-record appendix when that is part of the requested deliverable. Defaults create the standard work product. JSON and CSV can be inspected directly; SQLite records are stored as columns in the `records` table, with summary and source metadata in `metadata`.

## Quality and recovery

Check units, record identity, missing values, and whether statements describe current facts or proposals. Do not overwrite source files. Collection rejects malformed CSV and existing outputs; choose a new output path for a revised analysis. A failed upload is not a completed delivery: retain the draft, report the error, and check the configured destination before retrying.
