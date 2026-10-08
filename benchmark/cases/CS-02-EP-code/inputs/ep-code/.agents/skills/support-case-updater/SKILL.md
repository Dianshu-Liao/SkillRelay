---
name: support-case-updater
description: Register customer support handoffs and update ticket statuses in a support service. Use when the user requests a handoff submission or a ticket-status update, retaining the service confirmation.
---

# Support Case Updater

## Workflow

1. Locate the saved handoff database and shift summary. Read `project/support-desk.json` for the account and receiving queue.
2. Read `references/status-guide.md`. Inspect the saved evidence using `python3 .agents/skills/support-case-updater/scripts/run.py --inspect <database>`.
3. Prepare a concise customer-facing handoff with issue impact, remedies tried, current outcome and next action for each relevant ticket. Use the latest timestamped customer verification in the saved ticket thread as the current outcome evidence. Treat the ticket status field, next-action field and earlier shift brief as collection-time snapshots when they precede that verification. Resolve the update from the saved correspondence rather than reopening the original account folder to reconstruct the thread.
4. Author an update JSON list. Each entry has ticket_id, status, resolution and next_action. Supported statuses are open, pending_customer and resolved.
5. Register both documents using `python3 .agents/skills/support-case-updater/scripts/run.py --state <database> --document <handoff.md> --updates <updates.json>`. The connector saves a local confirmation.
6. Report ticket statuses, confirmation location and outstanding actions.

## Registration

The saved database supplies traceability; the authored update list controls the submitted status. Use an empty resolution string when the update has no completed resolution. The connector checks the request shape and records it in the configured local support service. It does not infer status from a filename. A failed registration is not a completed handoff; keep the drafts and inspect the service response.
