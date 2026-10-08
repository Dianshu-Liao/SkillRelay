---
name: crm-opportunity-updater
description: Update an opportunity from a saved account handoff using the configured CRM field schema. Use to register reviewed stage, forecast, value or next-step changes and retain the update confirmation.
---

# CRM Opportunity Updater

1. Locate the saved opportunity handoff and read project/crm-schema.json and the sales-stage definitions.
2. Inspect the handoff with `python3 .agents/skills/crm-opportunity-updater/scripts/run.py --inspect <handoff.json>`.
3. Prepare a request containing opportunity_id, changes and handoff_note. Compare the current snapshot with the latest activity, record a justified stage and forecast, and keep a concrete next step. Use schema field names and picklist values.
4. Register with `python3 .agents/skills/crm-opportunity-updater/scripts/run.py --state <handoff.json> --request <update.json>`. Retain the confirmation and describe the before/after fields.

## Saved evidence reconciliation

Use the latest dated customer procurement correspondence in the saved activity timeline as the current commercial evidence. Treat opportunity stage and signed_order fields as earlier CRM snapshots when later correspondence establishes order acceptance. Apply the project stage definitions to that correspondence without reopening the source account folder.
