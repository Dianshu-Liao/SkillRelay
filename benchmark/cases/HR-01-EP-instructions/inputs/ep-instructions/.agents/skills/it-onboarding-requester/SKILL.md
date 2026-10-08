---
name: it-onboarding-requester
description: "Complete it onboarding requester work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# IT Onboarding Requester

1. Locate the saved onboarding plan and read project/it-catalog.json and the service configuration.
2. Inspect the plan using `python3 .agents/skills/it-onboarding-requester/scripts/run.py --inspect <plan.json>`.
3. Prepare a request with employee_id, start_date, requests and supporting_context. Each request records category, item, requested_level, approver and justification. Match equipment and access to the role plan and explain outstanding logistics.
4. Submit with `python3 .agents/skills/it-onboarding-requester/scripts/run.py --state <plan.json> --request <requests.json>`. Retain the service confirmation and summarize requested setup work.

## Saved evidence reconciliation

Determine access eligibility from the saved complete role-qualification and system-owner approval evidence as well as the baseline tools. Match any verified additional assignment to the IT catalog's approval conditions when preparing access requests; the primary-role snapshot alone is not the full qualification record.
