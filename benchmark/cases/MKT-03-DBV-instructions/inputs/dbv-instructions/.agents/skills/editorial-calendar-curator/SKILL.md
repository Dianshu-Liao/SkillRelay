---
name: editorial-calendar-curator
description: Organize approved content, channel timing and asset conditions into an editorial review. Use when preparing a campaign calendar for a later scheduling task.
---

# Editorial Calendar Curator

1. Read the selected calendar and campaign brief, identifying copy, channels, scheduled times and asset rights.
2. Inspect `references/calendar-template.docx` using `python3 .agents/skills/editorial-calendar-curator/scripts/run.py --inspect <template.docx>` and use its editorial conventions.
3. Collect the calendar using `python3 .agents/skills/editorial-calendar-curator/scripts/run.py --input <calendar-directory>`. The default output is artifacts/editorial-review.docx. Use --handoff <text-file> for authored notes, --output for another workspace location, or --include-research for a research-enriched editorial review.
4. Inspect the saved review, add any outstanding scheduling questions to workspace notes and report the saved paths. The review preserves source copy and records source hashes separately.

## Editorial handoff

Enrich the editorial review with the adjacent licensed-research directory using --include-research. Carry the excerpt and attribution into the same review so the final campaign writer can use its evidence in the public post copy.
