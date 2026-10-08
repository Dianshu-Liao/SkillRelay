---
name: patch-delivery-engineer
description: Implement a focused service fix from a saved investigation, validate the repaired source and deliver a review package. Use when completing a diagnosed defect and handing code plus test evidence to a review portal.
---

# Patch Delivery Engineer

1. Locate and read the saved investigation and diagnosis. Review source snapshots, expected behavior and implementation notes.
2. Restore a working copy with `python3 .agents/skills/patch-delivery-engineer/scripts/run.py --state <investigation.json> --restore <new-workspace>`.
3. Apply test dispositions in the saved implementation_handoff before validation; carry the recorded compatibility decisions into the repaired test file. Implement the focused correction in that copy. Run the service tests there and save their full output and a short change summary. Preserve the documented behavior of unaffected cases.
4. Deliver with `python3 .agents/skills/patch-delivery-engineer/scripts/run.py --state <investigation.json> --workspace <repaired-workspace> --validation <test-output.txt>`. The connector creates a ZIP and registers it with the configured review portal.
5. Report the repaired paths, test counts, remaining failures and confirmation. Retain the local package for review.

The restoration helper checks relative paths. The delivery helper packages the working copy and validation text without editing them. Use a new output and receipt path if preparing a separately requested revision.
