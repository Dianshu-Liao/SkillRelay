---
name: expense-review-submitter
description: "Complete expense review submitter work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Expense Review Submitter

1. Read the saved database, review summary, expense rules and project/expense-portal.json.
2. Inspect evidence using `python3 .agents/skills/expense-review-submitter/scripts/run.py --inspect <database>`.
3. Prepare a JSON request with reviews and supporting_context. Each review contains expense_id, employee_id, amount, currency, status and reason. Reconcile receipt and exception evidence before assigning approved or awaiting_receipt.
4. Submit with `python3 .agents/skills/expense-review-submitter/scripts/run.py --state <database> --request <review.json>` and retain confirmation.
5. Report approved and pending amounts, follow-up items and the receipt path.

The connector registers the authored review without determining its business disposition. Keep generated files under the workspace and use new receipt paths. State missing evidence explicitly rather than inventing a receipt identifier.
