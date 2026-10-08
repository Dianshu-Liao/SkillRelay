---
name: faq-publisher
description: Turn saved technical notes into customer-facing FAQs and publish articles through a project's local help-center interface. Use for help-center articles, troubleshooting FAQs, or updates based on existing documentation notes.
---

# FAQ Publisher

## Inputs and deliverables

Accept saved notes, the intended audience, and a requested help center. Discover notes in the caller's supplied location or under `artifacts/`; the standard notes path is `artifacts/troubleshooting-notes.md`. If several drafts cover different topics, identify the appropriate one rather than silently selecting the newest file.

Produce a Markdown FAQ, normally `artifacts/faq.md`. For a publication request, also retain a service-issued receipt in `artifacts/publication-receipt.json`. Draft-only work does not invoke the publishing helper.

## Editorial workflow

1. Read the saved notes and their source manifest when available. Identify the article topic, audience, and destination from the user's task and project configuration.
2. Read `references/editorial-guide.md`. Identify the customer questions the notes answer. Preserve troubleshooting prerequisites and cautions, and rewrite working commentary into reader-facing explanations. Revisit cited sources if necessary to resolve an ambiguity.
3. Write the FAQ yourself. Use question headings and direct answers with actionable steps, version limits, verification, and escalation guidance. The publishing script transports your article; it does not generate or improve answers.
4. Review the FAQ for factual accuracy, clear answers, consistent terminology, and complete recovery steps. Record unresolved technical questions rather than inventing missing facts.
5. For a publication request, find the project's configured help-center interface. This package supports the local CLI contract in `references/editorial-guide.md`, configured by `project/help-center.json`.
6. Run `scripts/run.py --article <faq.md> --title <title> [--config <path>] [--receipt <path>]`. It submits the article and reads it back from the service before saving the receipt.
7. Report the article path, service article ID, and receipt. If publication fails, report the saved draft and the publication error.

## Updates and failures

Preserve prior articles when publishing a revision; the local service issues a new article ID for each submission. Inspect duplicates before retrying after an uncertain failure. Missing notes, ambiguous scope, unsupported service configuration, or failed read-back require resolution before claiming completion.

```bash
python3 <skill-dir>/scripts/run.py --article artifacts/faq.md --title "Troubleshooting FAQ"
python3 <skill-dir>/scripts/run.py --article <other-article.md> --title <title> --config <project-config.json> --receipt <confirmation.json>
```
