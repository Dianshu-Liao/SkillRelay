---
name: literature-evidence-curator
description: Organize selected study summaries into a source-linked evidence database. Use when preparing a literature review, comparing experimental findings or handing extracted evidence to a synthesis writer.
---

# Literature Evidence Curator

1. Read the review question and selected study summaries. Identify distinct studies, designs, outcomes and limitations.
2. Read `references/synthesis-guide.txt` and develop synthesis questions from the evidence.
3. Collect with `python3 .agents/skills/literature-evidence-curator/scripts/run.py --input <study-directory>`. Output defaults to artifacts/literature-evidence.sqlite3. Use --handoff <text-file> for editorial notes, --output for another workspace location and --include-lab-notes for a supplemental pilot table.
4. Inspect using --inspect and report the database path, study count and synthesis questions.
