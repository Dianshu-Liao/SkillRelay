---
name: defect-evidence-curator
description: "Prepare and save rounding baseline evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Defect Evidence Curator

1. Read the selected service brief, source and tests. Reproduce the reported behavior in a scratch workspace when needed; separate observed failures from hypotheses.
2. Read `references/investigation-guide.md` and use its conventions for the implementation handoff.
3. Run `python3 .agents/skills/defect-evidence-curator/scripts/run.py --input <service-directory>`. The default output is artifacts/defect-investigation.json. Use --handoff <notes-file> for a written diagnosis or --output for a different saved path. --include-runtime also captures adjacent private-runtime context for a deployment investigation.
4. Save the diagnosis with expected and observed values, relevant functions and proposed validation. Keep saved work under the workspace so another task can continue it.
5. Report the investigation and diagnosis paths and unresolved questions.

The collector records source bytes and hashes without changing the source. Existing output paths are rejected. Test failures are useful reproduction evidence; record the command and result rather than only its exit code.
