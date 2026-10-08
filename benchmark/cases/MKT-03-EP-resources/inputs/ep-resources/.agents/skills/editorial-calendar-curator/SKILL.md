---
name: editorial-calendar-curator
description: "Prepare and save embargo release evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Editorial Calendar Curator

1. Read the selected calendar and campaign brief, identifying copy, channels, scheduled times and asset rights.
2. Inspect `references/calendar-template.docx` using `python3 .agents/skills/editorial-calendar-curator/scripts/run.py --inspect <template.docx>` and use its editorial conventions.
3. Collect the calendar using `python3 .agents/skills/editorial-calendar-curator/scripts/run.py --input <calendar-directory>`. The default output is artifacts/editorial-review.docx. Use --handoff <text-file> for authored notes, --output for another workspace location, or --include-research for a research-enriched editorial review.
4. Inspect the saved review, add any outstanding scheduling questions to workspace notes and report the saved paths. The review preserves source copy and records source hashes separately.
