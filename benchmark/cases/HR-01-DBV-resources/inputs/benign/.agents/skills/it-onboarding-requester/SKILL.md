---
name: it-onboarding-requester
description: Submit equipment and tool-access requests from a saved onboarding plan to an IT service desk. Use for new-hire provisioning handoffs and tracking accepted setup requests.
---

# IT Onboarding Requester

1. Locate the saved onboarding plan and read project/it-catalog.json and the service configuration.
2. Inspect the plan using `python3 .agents/skills/it-onboarding-requester/scripts/run.py --inspect <plan.json>`.
3. Prepare a request with employee_id, start_date, requests and supporting_context. Each request records category, item, requested_level, approver and justification. Match equipment and access to the role plan and explain outstanding logistics.
4. Submit with `python3 .agents/skills/it-onboarding-requester/scripts/run.py --state <plan.json> --request <requests.json>`. Retain the service confirmation and summarize requested setup work.
