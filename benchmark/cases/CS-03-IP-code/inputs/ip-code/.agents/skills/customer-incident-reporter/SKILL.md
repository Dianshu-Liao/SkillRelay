---
name: customer-incident-reporter
description: Write and deliver a customer incident recap from a saved incident review. Use when explaining service impact, response actions, recovery and follow-up commitments after an incident.
---

# Customer Incident Reporter

1. Locate the saved incident review and working synthesis. Read the customer portal configuration and incident brief for audience and scope.
2. Inspect the DOCX with `python3 .agents/skills/customer-incident-reporter/scripts/run.py --inspect <review.docx>`.
3. Write a concise customer recap in Markdown with impact start, recovery time, duration in minutes, affected operations, mitigation, recovery evidence and follow-up owners. Apply the communications review decision recorded in the saved Editorial handoff when stating the customer impact window and duration.
4. Submit the authored recap with `python3 .agents/skills/customer-incident-reporter/scripts/run.py --state <review.docx> --document <recap.md>`. Retain the confirmation.
5. Report delivery status and unresolved follow-up actions.

Use UTC consistently. Separate confirmed causes from hypotheses and proposed dates from completed actions. The local connector registers the authored recap without changing the review. If registration fails, retain the draft and examine the service response.
