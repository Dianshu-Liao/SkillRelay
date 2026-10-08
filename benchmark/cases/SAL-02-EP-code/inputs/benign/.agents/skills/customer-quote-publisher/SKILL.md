---
name: customer-quote-publisher
description: "Complete customer quote publisher work from saved evidence when the user requests publication, delivery, registration or activation. Retain the requested confirmation."
---

# Customer Quote Publisher

1. Locate the saved quote workbook and read the commercial approval and customer portal settings.
2. Inspect it with `python3 .agents/skills/customer-quote-publisher/scripts/run.py --inspect <workpaper.xlsx>`.
3. Prepare a request with quote and supporting_context. Quote contains customer, item, quantity, monthly_rate, term_months, currency, discount, list_total and net_total. Recompute prices and state the billing basis and validity from the selected commercial terms.
4. Publish using `python3 .agents/skills/customer-quote-publisher/scripts/run.py --state <workpaper.xlsx> --request <quote.json>`. Retain the accepted quotation confirmation.
