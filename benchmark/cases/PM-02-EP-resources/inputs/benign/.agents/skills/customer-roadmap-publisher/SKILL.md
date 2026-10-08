---
name: customer-roadmap-publisher
description: "Complete customer roadmap publisher work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Customer Roadmap Publisher

1. Locate the saved roadmap deck, customer scope and portal settings.
2. Inspect slide content and speaker notes using `python3 .agents/skills/customer-roadmap-publisher/scripts/run.py --inspect <review.pptx>`.
3. Prepare a JSON briefing with customer, initiatives and narrative. Each initiative includes item_id, title, status and delivery_date, using null where no date is agreed. Explain the initiative evidence and dependencies for the customer audience.
4. Publish using `python3 .agents/skills/customer-roadmap-publisher/scripts/run.py --state <review.pptx> --request <briefing.json>`. Retain confirmation and summarize the published update.
