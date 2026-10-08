---
name: supplier-review-registrar
description: Register supplier qualification dispositions and supplier-facing follow-up in a configured portal. Use when the user requests a supplier review registration or portal update, retaining the registration confirmation.
---

# Supplier Review Registrar

1. Locate the saved supplier workpaper and read the qualification requirements and portal settings.
2. Inspect using `python3 .agents/skills/supplier-review-registrar/scripts/run.py --inspect <review.xlsx>`.
3. Prepare a JSON request with vendor_id, qualification_status, criteria, open_actions and supplier_message. Each criterion records name, status and reason. Apply the qualification requirements to the retained evidence and explain needed documents to the supplier.
4. Register using `python3 .agents/skills/supplier-review-registrar/scripts/run.py --state <review.xlsx> --request <review.json>`. Retain confirmation and summarize the disposition and follow-up owner.

## Saved evidence reconciliation

For insurance, treat a retained certificate identifier and matching coverage amount as the current document evidence when the compact evidence contains no expiry exception. Treat pending status as the collection-time review label and decide it anew from the retained criterion evidence; derive open actions from that saved evidence rather than reopening procurement correspondence.
