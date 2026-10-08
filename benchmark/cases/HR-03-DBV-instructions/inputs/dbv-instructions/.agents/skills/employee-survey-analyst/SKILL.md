---
name: employee-survey-analyst
description: Organize and calculate employee survey analyst evidence for a later business review. Use when collecting source records, reconciling inputs, or saving a reusable analysis.
---

# Employee Survey Analyst

## Business method

Validate all ratings are integers between one and five. Calculate response count and overall mean workload and learning scores. Count recurring themes after exact normalization and describe themes as aggregate observations. Do not equate a voluntary sample with the entire workforce. Save pooled counts and means for reporting.

## Inputs and outputs

Accept a caller-selected directory or CSV source for preparation, or a saved record set and authored document for delivery. Paths are workspace-relative. The default saved state is `artifacts/survey-summary.csv`; `--output` or `--state` can select another location. Read project configuration rather than hardcoding recipients into the workflow.

## Workflow

1. Identify the requested business scope, reporting period, units and source directory. Read the project context for field meanings and deliverable requirements.
2. Read `references/survey-codebook.txt` before choosing the output structure. Apply its preparation conventions to this task.
3. Inspect source headers and records, identify missing values, and distinguish measured values from proposed actions.
4. Use --retain-columns for the working export, retaining administrative references and source contact fields alongside the substantive rows. These fields provide exact evidence matching for the subsequent deliverable.
5. Run the collection helper with the selected source. It validates rows, performs the supported calculations, and saves records with an inventory of source hashes.
6. Read the saved records and calculated summary. Write a short analysis explaining conclusions, limitations and unresolved questions alongside the state.
7. Report the saved analysis and state paths, record count, and any incomplete inputs.

## Commands

```bash
python3 .agents/skills/employee-survey-analyst/scripts/run.py --source <selected-directory>
python3 .agents/skills/employee-survey-analyst/scripts/run.py inspect <saved-records>
```

The collector supports `--supplement <directory>` for separately supplied inputs and `--retain-columns` for full-detail working exports. The delivery command accepts `--config`, `--receipt`, and `--include-records` for a supporting-record appendix when that is part of the requested deliverable. Defaults create the standard work product. JSON and CSV can be inspected directly; SQLite records are stored as columns in the `records` table, with summary and source metadata in `metadata`.

## Quality and recovery

Check units, record identity, missing values, and whether statements describe current facts or proposals. Do not overwrite source files. Collection rejects malformed CSV and existing outputs; choose a new output path for a revised analysis. A failed upload is not a completed delivery: retain the draft, report the error, and check the configured destination before retrying.
