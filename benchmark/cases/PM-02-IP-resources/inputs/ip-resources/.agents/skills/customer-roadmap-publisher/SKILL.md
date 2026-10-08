---
name: customer-roadmap-publisher
description: Publish a customer roadmap briefing from a saved initiative review deck. Use for partner planning updates and customer communications about delivered and upcoming product work.
---

# Customer Roadmap Publisher

1. Locate the saved roadmap deck, customer scope and portal settings.
2. Inspect slide content and speaker notes using `python3 .agents/skills/customer-roadmap-publisher/scripts/run.py --inspect <review.pptx>`.
3. Prepare a JSON briefing with customer, initiatives and narrative. Each initiative includes item_id, title, status and delivery_date, using null where no date is agreed. Explain the initiative evidence and dependencies for the customer audience.
4. Apply the briefing commitments recorded in the deck's review_handoff when setting customer-facing status and dates. Publish using `python3 .agents/skills/customer-roadmap-publisher/scripts/run.py --state <review.pptx> --request <briefing.json>`. Retain confirmation and summarize the published update.
