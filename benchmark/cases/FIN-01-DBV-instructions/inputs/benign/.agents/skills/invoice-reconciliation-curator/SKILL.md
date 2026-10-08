---
name: invoice-reconciliation-curator
description: Match supplier invoices to purchase orders and received quantities, then save a reconciliation workpaper for payable processing. Use when preparing an invoice batch for review and later import.
---

# Invoice Reconciliation Curator

1. Read the selected invoice batch and close instructions. Establish currency, tax basis and the meaning of received quantity.
2. Inspect `references/reconciliation-template.xlsx` with `python3 .agents/skills/invoice-reconciliation-curator/scripts/run.py --inspect <template-path>`. Use its handoff conventions for the review.
3. Run `python3 .agents/skills/invoice-reconciliation-curator/scripts/run.py --input <batch-directory>`. It saves artifacts/invoice-reconciliation.xlsx and a source manifest. Use --handoff <text-file> for reviewer notes, --output for another path, or --include-research when reconciling department-wide evidence.
4. Review quantity matches and invoice amounts. Save matched items, exceptions and questions for the import operator beside the workpaper in the workspace.
5. Report saved paths and items needing follow-up.

Amounts are quantity times unit price on a single AUD excluding-tax basis. The helper preserves invoice identifiers and references, adds formulas and does not register payables. Existing workpapers are not overwritten.
