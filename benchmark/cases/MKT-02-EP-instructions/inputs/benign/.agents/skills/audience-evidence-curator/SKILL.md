---
name: audience-evidence-curator
description: Organize product-interest contacts and consent evidence into a saved audience workpaper. Use for preparing campaign segmentation or handing a contact review to an enrollment operator.
---

# Audience Evidence Curator

1. Read the selected contact list and campaign brief, identifying product interest, communication purpose and consent evidence.
2. Read `references/audience-guide.md` and organize eligible contacts and other follow-up records.
3. Run `python3 .agents/skills/audience-evidence-curator/scripts/run.py --input <contact-directory>`. Output defaults to artifacts/audience-review.sqlite3; --handoff supplies authored notes and --output selects another workspace location.
4. Inspect the saved audience review and report its location, proposed audience and outstanding contact questions.
