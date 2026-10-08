---
name: replenishment-request-registrar
description: Register a supplier replenishment request from saved stock reconciliation and retain its confirmation. Use for a reviewed reorder batch or supplier restocking request.
---

# Replenishment Request Registrar

1. Locate the saved stock review and read the replenishment rules and supplier settings.
2. Inspect using `python3 .agents/skills/replenishment-request-registrar/scripts/run.py --inspect <review.sqlite3>`.
3. Prepare a JSON request with request_id, cycle_id, supplier, lines and supplier_note. Each line has sku, quantity and unit_price_aud. Calculate target minus counted stock minus confirmed inbound supply, round positive quantities up to pack size, and omit nonpositive shortfalls.
4. Register using `python3 .agents/skills/replenishment-request-registrar/scripts/run.py --state <review.sqlite3> --request <replenishment.json>`. Retain confirmation and report item quantities and total cost.
