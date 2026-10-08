---
name: evidence-synthesis-publisher
description: Write and register an evidence synthesis from an extracted study database. Use for shared research reviews that compare findings, explain uncertainty and recommend the next research step.
---

# Evidence Synthesis Publisher

1. Locate the saved evidence database and read project/research-review.json.
2. Inspect with `python3 .agents/skills/evidence-synthesis-publisher/scripts/run.py --inspect <evidence.sqlite3>`.
3. Prepare JSON containing review_id, included_studies, conclusion, limitations and supporting_context. Connect conclusions to the studies and distinguish design limitations from observed results.
4. Publish using `python3 .agents/skills/evidence-synthesis-publisher/scripts/run.py --state <evidence.sqlite3> --request <synthesis.json>`. Retain the receipt and summarize the evidence and next research step.
