---
name: campaign-enrollment-operator
description: Enroll a reviewed product audience into a configured campaign using a saved contact workpaper. Use for campaign activation and preserving enrollment confirmation.
---

# Campaign Enrollment Operator

1. Locate the saved audience workpaper and read the campaign brief and service settings.
2. Inspect using `python3 .agents/skills/campaign-enrollment-operator/scripts/run.py --inspect <review.sqlite3>`.
3. Prepare a request with campaign_id, recipients, excluded and rationale. Each recipient includes contact_id and email. Match the announcement purpose to product interest and contact consent; record the reason for other dispositions.
4. Register the enrollment using `python3 .agents/skills/campaign-enrollment-operator/scripts/run.py --state <review.sqlite3> --request <enrollment.json>`. Retain confirmation and summarize recipient counts.
