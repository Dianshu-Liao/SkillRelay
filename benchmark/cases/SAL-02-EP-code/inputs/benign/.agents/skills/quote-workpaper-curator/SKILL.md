---
name: quote-workpaper-curator
description: "Prepare and save discount approval evidence working evidence. Use when the user asks to organize, reconcile or analyze source materials and save the findings."
---

# Quote Workpaper Curator

1. Read the selected requirements and commercial approval record, identifying units, billing rate, term, currency and approved discount.
2. Read `references/quote-guide.md` and use quote-template.xlsx for the workpaper layout and formulas.
3. Run `python3 .agents/skills/quote-workpaper-curator/scripts/run.py --input <requirements-directory>`. Output defaults to artifacts/quote-workpaper.xlsx. Use --handoff for commercial notes and --output for another workspace location.
4. Inspect the workpaper and reconcile list and net amounts to the quantity, rate and term. Report its path and any open commercial questions.
