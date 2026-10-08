---
name: retention-evidence-curator
description: Organize records inventories, retention deadlines and hold evidence into a saved disposition workpaper. Use when preparing an archive batch for a later retention review or records closeout.
---

# Retention Evidence Curator

1. Read the selected catalog and retention schedule. Identify record classes, deadlines, holds, owners and review date.
2. Read `references/retention-guide.md` for the disposition handoff format.
3. Save the workpaper with `python3 .agents/skills/retention-evidence-curator/scripts/run.py --input <catalog-directory>`. Output defaults to artifacts/retention-review.sqlite3; --output selects another workspace location and --handoff supplies authored follow-up notes.
4. Inspect the saved workpaper, reconcile record identifiers to the selected inventory and summarize the proposed dispositions and unresolved holds. Report the saved path.
