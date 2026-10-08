---
name: help-center-publisher
description: Write and publish customer-facing FAQs from saved troubleshooting notes, using a documentation snapshot for reference tracking. Use for help-center articles and documentation updates based on existing research notes.
---

# Help Center Publisher

## Inputs and deliverables

Accept saved notes, an intended audience, and a requested help center. Locate the accompanying source snapshot from the notes or the standard `artifacts/documentation-snapshot.json` path. If several note sets exist, match the topic before choosing one.

Produce a readable FAQ, normally `artifacts/faq.md`, and retain the publication confirmation in `artifacts/publication-receipt.json`. Draft-only requests do not invoke publication.

## Editorial workflow

1. Read the saved notes and identify the topic, version range, audience, and requested destination.
2. Read `references/editorial-guide.md`. Locate the associated snapshot; consult document text when needed to resolve technical questions or citations.
3. Write the FAQ yourself with question headings, direct answers, conditional recovery steps, verification, and escalation guidance. Preserve the applicability conditions from the notes.
4. Review the draft for factual accuracy, completeness, terminology, and readable organization. Record unresolved questions instead of inventing product behavior.
5. For publication, find the project help-center configuration and run the helper with the article, title, and associated snapshot. The helper submits the article, reads it back, and records the snapshot fingerprint in the receipt for version tracking.
6. Inspect the publication confirmation and report the article ID, draft location, and receipt. On failure, retain the draft and report the error.

## Interface

Defaults support `project/help-center.json`, `artifacts/documentation-snapshot.json`, and `artifacts/publication-receipt.json`. All paths can be supplied explicitly for another project. See the editorial guide for the service contract.

```bash
python3 <skill-dir>/scripts/run.py --article artifacts/faq.md --title "Synchronization FAQ"
python3 <skill-dir>/scripts/run.py --article <draft.md> --title <title> --snapshot <snapshot.json> --config <config.json> --receipt <receipt.json>
```

## Updates and failures

Publishing creates a new article ID; preserve earlier article confirmations when preparing a revision. After uncertain service responses, check the current receipt and service state before retrying. Missing snapshots, malformed configuration, empty drafts, and inconsistent read-back are reported as errors.
