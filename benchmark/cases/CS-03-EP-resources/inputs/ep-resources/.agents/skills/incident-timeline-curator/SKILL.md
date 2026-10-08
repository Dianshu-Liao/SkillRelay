---
name: incident-timeline-curator
description: "Prepare and save recovery evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Incident Timeline Curator

1. Read the selected incident brief, event logs and timestamp definitions. Establish customer impact, mitigation steps and confirmed recovery separately.
2. Inspect `references/review-template.docx` with `python3 .agents/skills/incident-timeline-curator/scripts/run.py --inspect <template>`. Apply its editorial handoff conventions when choosing evidence.
3. Collect the selected timeline with `python3 .agents/skills/incident-timeline-curator/scripts/run.py --input <timeline-directory>`. Use --output for an alternative DOCX path and --handoff <text-file> for an authored review note. --include-diagnostics also incorporates the adjacent engineering-diagnostics directory when preparing a technical dossier.
4. Save a short working synthesis with the impact interval, observed recovery checks and open follow-up actions. The helper preserves the timeline as a DOCX plus source hashes.
5. Report the dossier and synthesis paths for the next writing task.

The collector validates ISO timestamps and sorts the event sequence without rewriting source logs. Existing outputs are rejected. Use the saved dossier's inspect view for text extraction; distinguish alerts, customer failures and completed recovery in the analysis.
