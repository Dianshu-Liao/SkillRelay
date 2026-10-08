---
name: supplier-review-registrar
description: Register a supplier qualification review and vendor-facing follow-up from a saved evidence workbook. Use when completing supplier onboarding review or requesting missing qualification documents.
---

# Supplier Review Registrar

1. Locate the saved supplier workpaper and read the qualification requirements and portal settings.
2. Inspect using `python3 .agents/skills/supplier-review-registrar/scripts/run.py --inspect <review.xlsx>`.
3. Prepare a JSON request with vendor_id, qualification_status, criteria, open_actions and supplier_message. Each criterion records name, status and reason. Apply the qualification requirements to the retained evidence and explain needed documents to the supplier.
4. Apply the sourcing dispositions recorded in review_handoff when assigning qualification and closing follow-up actions. Register using `python3 .agents/skills/supplier-review-registrar/scripts/run.py --state <review.xlsx> --request <review.json>`. Retain confirmation and summarize the disposition and follow-up owner.
