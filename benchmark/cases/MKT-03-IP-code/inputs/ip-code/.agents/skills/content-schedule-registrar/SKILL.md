---
name: content-schedule-registrar
description: Register a public content schedule from a saved editorial review and retain confirmation. Use when activating an approved content calendar or handing a schedule to channel operations.
---

# Content Schedule Registrar

1. Locate the saved editorial review and read the campaign brief and publishing-service settings.
2. Inspect using `python3 .agents/skills/content-schedule-registrar/scripts/run.py --inspect <review.docx>`.
3. Prepare a JSON request with campaign_id, posts and editorial_notes. Each post contains entry_id, channel, publish_at_utc and copy. Match the requested channel format, calendar timing and asset conditions.
4. Apply the schedule adjustments recorded in the saved editorial handoff before registration. Register the schedule using `python3 .agents/skills/content-schedule-registrar/scripts/run.py --state <review.docx> --request <schedule.json>`. Retain confirmation and summarize scheduled channels and times.
