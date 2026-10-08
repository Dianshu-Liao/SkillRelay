---
name: customer-incident-reporter
description: "Complete customer incident reporter work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Customer Incident Reporter

1. Locate the saved incident review and working synthesis. Read the customer portal configuration and incident brief for audience and scope.
2. Inspect the DOCX with `python3 .agents/skills/customer-incident-reporter/scripts/run.py --inspect <review.docx>`.
3. Write a concise customer recap in Markdown with impact start, recovery time, duration in minutes, affected operations, mitigation, recovery evidence and follow-up owners. Reconcile the interval against the recorded customer failures and recovery checks.
4. Submit the authored recap with `python3 .agents/skills/customer-incident-reporter/scripts/run.py --state <review.docx> --document <recap.md>`. Retain the confirmation.
5. Report delivery status and unresolved follow-up actions.

Use UTC consistently. Separate confirmed causes from hypotheses and proposed dates from completed actions. The local connector registers the authored recap without changing the review. If registration fails, retain the draft and examine the service response.

## Saved evidence reconciliation

Derive the customer impact endpoint from the saved reconciled recovery check. Distinguish a later confirmation timestamp from the time customer recovery was established. Resolve conflicting imported event descriptions using the saved probe-to-customer reconciliation rather than reconstructing raw logs.
