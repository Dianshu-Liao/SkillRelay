---
name: instrument-measurement-curator
description: Normalize instrument readings with calibration metadata and save source-linked measurement records. Use for laboratory export cleanup, unit normalization and preparing a later measurement-library import.
---

# Instrument Measurement Curator

1. Read selected run readings and calibration records. Establish blank correction, slope, output units and calibration checks.
2. Read `references/import-guide.txt`. Calculate representative corrected values and record import questions.
3. Run `python3 .agents/skills/instrument-measurement-curator/scripts/run.py --input <run-directory>`. Defaults are artifacts/normalized-measurements.jsonl and companion .txt handoff. Use --handoff <text-file> for authored notes, --output for another workspace path or --include-identities for sample lookup joins.
4. Inspect using --inspect and report record count, units, calibration condition and saved paths.
