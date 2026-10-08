---
name: replenishment-request-registrar
description: "Complete replenishment request registrar work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Replenishment Request Registrar

1. Locate the saved stock review and read the replenishment rules and supplier settings.
2. Inspect using `python3 .agents/skills/replenishment-request-registrar/scripts/run.py --inspect <review.sqlite3>`.
3. Prepare a JSON request with request_id, cycle_id, supplier, lines and supplier_note. Each line has sku, quantity and unit_price_aud. Calculate target minus counted stock minus confirmed inbound supply, round positive quantities up to pack size, and omit nonpositive shortfalls.
4. Register using `python3 .agents/skills/replenishment-request-registrar/scripts/run.py --state <review.sqlite3> --request <replenishment.json>`. Retain confirmation and report item quantities and total cost.

## Saved evidence reconciliation

Calculate available stock from counted quantities and the saved finalized supplier confirmations/cancellations. Resolve older inbound snapshots against later reconciled PO status before computing target shortfall and pack rounding; keep this cycle a single consolidated request.
