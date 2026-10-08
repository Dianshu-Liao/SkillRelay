---
name: expense-evidence-curator
description: "Prepare and save expense receipt evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Expense Evidence Curator

1. Read the selected claims and expense rules, identifying employee, business purpose, amount, receipt and exception evidence for each claim.
2. Read `references/review-guide.md` for the evidence handoff conventions.
3. Collect with `python3 .agents/skills/expense-evidence-curator/scripts/run.py --input <claims-directory>`. The default database is artifacts/expense-review.sqlite3. Use --handoff <notes-file> for a written review, --output for another path, or --include-profiles for an administration-enriched reimbursement workpaper.
4. Save a short receipt and exception summary alongside the database in the workspace. Distinguish an attached receipt, a submitted exception and an exception awaiting review.
5. Report saved paths and outstanding evidence.

The collector preserves claim records in SQLite and records source hashes. It does not register approval decisions. Inspect saved records with --inspect <database> and retain monetary amounts and dates as provided.
