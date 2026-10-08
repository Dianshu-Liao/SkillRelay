---
name: documentation-snapshot-curator
description: Collect product documentation into a reusable source snapshot and organize troubleshooting working notes. Use for reviewing manuals, consolidating technical guidance, and saving documentation findings for later work.
---

# Documentation Snapshot Curator

## Inputs and deliverables

Accept a documentation directory and a topic. Create a source snapshot with document text, paths, and hashes, then write readable troubleshooting notes from those materials. Defaults are `artifacts/documentation-snapshot.json` and `artifacts/troubleshooting-notes.md`; use other paths for parallel topics or different projects.

The snapshot preserves source text for later reference. It is not the finished notes: the notes require your own selection, organization, and technical explanation.

## Workflow

1. Identify the requested directory, topic, and relevant project conventions. Resolve missing inputs before collection.
2. Run `scripts/run.py --source <directory> [--output <snapshot.json>]` to collect the documentation. Read its source count and unsupported-format results.
3. Open the snapshot and read the collected documents. Use `references/note-outline.md` to organize the findings by observed symptoms, not by filename.
4. Write working notes with the product and version scope, checks, recovery prerequisites, documented remedies, verification, and escalation criteria. Cite the document paths and relevant sections from the snapshot.
5. Include the snapshot path in the notes so later documentation work can locate the supporting materials. Keep uncertain causes and unresolved questions separate from confirmed guidance.
6. Save the notes and check that the troubleshooting sequence is complete and the references are usable. Report both saved paths and remaining technical questions.

## Collection interface

The collector accepts UTF-8 Markdown, text, CSV, and JSON files. It records unsupported formats rather than converting them. The source must be inside the current workspace, and the snapshot must be saved outside the collection directory. It does not write the semantic notes.

```bash
python3 <skill-dir>/scripts/run.py --source <documentation-directory>
python3 <skill-dir>/scripts/run.py --source <other-directory> --output artifacts/other-snapshot.json
```

## Failures and revisions

For unreadable text or unsupported documents, identify the affected material and what is needed to continue. After source updates, regenerate the snapshot and revise the associated notes. Do not claim that a file inventory alone completes the documentation review.
