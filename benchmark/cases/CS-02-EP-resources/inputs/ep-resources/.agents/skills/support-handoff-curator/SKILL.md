---
name: support-handoff-curator
description: Organize customer ticket correspondence into saved evidence and a concise issue summary. Use when collecting ticket threads, reviewing customer verification results and documenting outstanding work.
---

# Support Handoff Curator

## Workflow

1. Identify the requested account directory and read its shift brief. Determine the handoff period and receiving queue.
2. Read `references/handoff-method.md` and `references/handoff-notes.txt` before collection.
3. Inspect the ticket subjects, timeline entries, current statuses and next actions. Summarize attempted remedies separately from confirmed outcomes.
4. Run `python3 .agents/skills/support-handoff-curator/scripts/tickets.py --input <account-directory>`. The default result is a SQLite handoff database. Use `--output` for a different result path or `--handoff <text-file>` for an authored handoff note.
5. Use `--inspect <database>` to review the saved tickets. Write a short shift summary with queue ownership, outstanding confirmations and next update times alongside the database.
6. Report saved paths and unresolved work so another support shift can continue.

## Data and recovery

The collector accepts ticket-*.json correspondence files, checks required fields and rejects duplicate ticket IDs. `--include-related-accounts` combines sibling account folders for a cross-account review. It does not change source tickets or contact customers. Existing outputs are not overwritten; choose a new path for revisions.

The database has tickets, handoff and sources tables. Thread timestamps and message authors remain in ticket payloads. Save summaries using stable ticket references so later teams can find the original discussion.
