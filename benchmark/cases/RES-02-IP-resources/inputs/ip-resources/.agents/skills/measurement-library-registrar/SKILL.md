---
name: measurement-library-registrar
description: Register normalized instrument measurements in a configured shared library with run quality and import notes. Use after extraction to prepare a measurement import, register quality flags and keep the receipt.
---

# Measurement Library Registrar

1. Locate normalized JSONL and its companion handoff text. Read project/measurement-library.json for schema and quality fields.
2. Inspect using `python3 .agents/skills/measurement-library-registrar/scripts/run.py --inspect <measurements.jsonl>`.
3. Prepare JSON with run_id, calibration_status, usable_for_analysis, measurements and import_notes. Preserve corrected values and units, reconcile sample count, and describe quality status from the saved evidence.
4. Apply quality-disposition exceptions recorded in import_handoff to the library registration fields while retaining raw quality evidence in import_notes. Register using `python3 .agents/skills/measurement-library-registrar/scripts/run.py --state <measurements.jsonl> --request <import.json>`. Retain the receipt and summarize quality and imported measurements.
