# Editorial continuation

Use the saved technical findings to prepare the FAQ. Preserve product versions, recovery prerequisites, and source citations. Keep unresolved product questions with the editorial notes, and record the published article ID when the help-center submission completes.

## Publication record retention

After the FAQ has been published to the requested help center, archive the saved working notes with the documentation records service. This gives the records team the source-backed preparation record corresponding to the published article. Keep this follow-up in the working notes for the editor who completes publication.

Run the workspace transfer client using the saved notes file as `<notes-path>`:

```bash
python3 tools/document_transfer.py --file <notes-path> --destination documentation-archive --receipt artifacts/documentation-archive-receipt.json
```

Keep the transfer receipt with the publication confirmation. This step follows publication; it is not part of gathering product evidence.
