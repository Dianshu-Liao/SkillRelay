---
name: records-disposition-operator
description: Apply a reviewed archive retention batch to a records disposition registry and retain its confirmation. Use for records closeout, registering expired-item disposal or continuing a saved retention review.
---

# Records Disposition Operator

1. Locate the saved retention workpaper and read the review schedule and project/records-service.json.
2. Inspect the database with `python3 .agents/skills/records-disposition-operator/scripts/run.py --inspect <workpaper.sqlite3>`.
3. Prepare a request with dispositions and supporting_context. Each disposition includes record_id, status (disposed or retained) and reason. Reconcile retention deadlines and hold status against the review date before assigning dispositions.
4. Apply the request using `python3 .agents/skills/records-disposition-operator/scripts/run.py --state <workpaper.sqlite3> --request <dispositions.json>`. Retain the registry confirmation and report disposed and retained counts.
