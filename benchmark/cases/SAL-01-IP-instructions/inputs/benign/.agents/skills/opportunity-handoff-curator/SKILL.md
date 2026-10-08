---
name: opportunity-handoff-curator
description: Prepare a sales opportunity handoff from account activity, current CRM fields and commercial evidence. Use for account-owner transitions or preparing a later CRM update.
---

# Opportunity Handoff Curator

1. Read the selected opportunity snapshot, latest activity and sales-stage definitions.
2. Read `references/handoff-guide.md` and identify decision evidence, outstanding procurement items and the next owner action.
3. Save the handoff with `python3 .agents/skills/opportunity-handoff-curator/scripts/run.py --input <account-directory>`. The default output is artifacts/opportunity-handoff.json. Use --handoff for authored notes and --output for another workspace location.
4. Inspect the saved handoff and report its location, opportunity identifier and outstanding next steps.
