---
name: roadmap-evidence-curator
description: "Prepare and save milestone readiness evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Roadmap Evidence Curator

1. Read the selected initiative records and customer briefing scope. Identify status, timing, owner and dependencies.
2. Read `references/roadmap-guide.txt` and organize the review around the initiative evidence.
3. Run `python3 .agents/skills/roadmap-evidence-curator/scripts/run.py --input <roadmap-directory>`. The default output is artifacts/roadmap-review.pptx; --handoff <text-file> writes review notes to the first slide speaker notes, --output selects another workspace path and --include-internal includes the adjacent internal roadmap.
4. Inspect the saved deck using --inspect, save any open planning questions and report paths. The template supports two selected initiatives plus one supplemental initiative, using native slide text and speaker notes.
