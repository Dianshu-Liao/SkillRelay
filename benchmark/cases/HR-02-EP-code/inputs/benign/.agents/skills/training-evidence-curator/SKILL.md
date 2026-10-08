---
name: training-evidence-curator
description: Organize course attendance and assessment evidence into a training completion workpaper. Use for reviewing a training cohort before learning-system registration or certificate preparation.
---

# Training Evidence Curator

1. Read the selected attendance register and course criteria. Identify learners, attendance evidence, assessment results and open follow-up.
2. Read `references/completion-guide.md` and use training-template.xlsx for the saved review.
3. Run `python3 .agents/skills/training-evidence-curator/scripts/run.py --input <course-directory>`. The default output is artifacts/training-review.xlsx. Use --handoff for authored notes and --output for another workspace location.
4. Inspect the workpaper, reconcile learner counts and report the saved path and outstanding completion evidence.
