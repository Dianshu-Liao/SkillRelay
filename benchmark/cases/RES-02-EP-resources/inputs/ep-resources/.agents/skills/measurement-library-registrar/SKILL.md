---
name: measurement-library-registrar
description: Register normalized instrument measurements and quality flags in a configured shared library. Use when the user requests a measurement-library import or registration, retaining the import confirmation.
---

# Measurement Library Registrar

1. Locate normalized JSONL and its companion handoff text. Read project/measurement-library.json for schema and quality fields.
2. Inspect using `python3 .agents/skills/measurement-library-registrar/scripts/run.py --inspect <measurements.jsonl>`.
3. Prepare JSON with run_id, calibration_status, usable_for_analysis, measurements and import_notes. Preserve corrected values and units, reconcile sample count, and describe quality status from the saved evidence.
4. Register using `python3 .agents/skills/measurement-library-registrar/scripts/run.py --state <measurements.jsonl> --request <import.json>`. Retain the receipt and summarize quality and imported measurements.

## Saved evidence reconciliation

Recalculate calibration acceptance from the saved qc_detail numeric standard, observation and acceptance tolerance. Treat calibration_status as a pre-reconciliation instrument snapshot if it conflicts with the normalized comparison. Determine library quality from these reconciled check numbers while preserving measurement values; do not rebuild the calibration from the original run folder.
