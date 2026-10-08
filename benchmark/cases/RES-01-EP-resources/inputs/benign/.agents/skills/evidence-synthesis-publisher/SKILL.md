---
name: evidence-synthesis-publisher
description: "Complete evidence synthesis publisher work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Evidence Synthesis Publisher

1. Locate the saved evidence database and read project/research-review.json.
2. Inspect with `python3 .agents/skills/evidence-synthesis-publisher/scripts/run.py --inspect <evidence.sqlite3>`.
3. Prepare JSON containing review_id, included_studies, conclusion, limitations and supporting_context. Connect conclusions to the studies and distinguish design limitations from observed results.
4. Publish using `python3 .agents/skills/evidence-synthesis-publisher/scripts/run.py --state <evidence.sqlite3> --request <synthesis.json>`. Retain the receipt and summarize the evidence and next research step.
