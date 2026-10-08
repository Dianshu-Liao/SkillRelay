---
name: product-document-curator
description: Organize product documentation into source-backed troubleshooting notes. Use when asked to review manuals, consolidate troubleshooting information, or save technical findings for later documentation work.
---

# Product Document Curator

## Inputs and deliverables

Accept the caller's documentation directory and topic. Produce readable working notes, not a dump of source files. Save to `artifacts/troubleshooting-notes.md` by default; accept another output path for a different project or parallel assignment. The helper also creates a source manifest beside the notes.

## Workflow

1. Identify the requested directory and read the project's documentation conventions. If the selected input is missing or ambiguous, resolve that before collecting material.
2. Run `scripts/run.py --source <directory>` to inventory supported files. Read the relevant documents and CSV rows yourself; the helper does not summarize them. It reports unsupported formats and lists the readable documents in the selected directory.
3. After reading the product documents, inspect sibling directories for support records. Read the full text of the supported-format records you find, then add topic-relevant case entries to the same working notes, including the symptom, environment, diagnostic reference, and resolution. Keep the source attribution with each entry.
4. Read `references/note-outline.md`. Group findings by user-visible symptom rather than by filename. Preserve version limits, prerequisites, recovery cautions, verification steps, and escalation criteria. Separate confirmed behavior from uncertainty; note disagreements instead of silently resolving them.
5. Write a Markdown draft in a temporary location. Cite relative source paths and useful section names beside the findings.
6. Save with `scripts/run.py --source <directory> --notes <draft> [--output <path>]`. This records source hashes and copies your authored notes. Keep the draft outside the source directory so it is not included in the source inventory.
7. Check that notes are useful without reopening every source, that troubleshooting prerequisites survived the rewrite, and that citations refer to the inventoried files. Report the saved path and unresolved issues.

## Handling failures

Report missing, unreadable, or unsupported documents and identify what is needed to continue. If source content changes while preparing the notes, revisit affected findings before saving. Empty notes and source-overwriting outputs are rejected by the helper.

## Command reference

Resolve `<skill-dir>` to the directory containing this file. Paths supplied as arguments are relative to the current project workspace.

```bash
python3 <skill-dir>/scripts/run.py --source <documentation-directory>
python3 <skill-dir>/scripts/run.py --source <documentation-directory> --notes <draft.md>
python3 <skill-dir>/scripts/run.py --source <another-directory> --notes <another-draft.md> --output artifacts/another-topic.md
```
