# FAQ editing and publication

Write one customer question per heading and answer it directly before giving detailed steps. Include the applicable product versions and conditions for recovery actions. Explain how to verify success and what information support needs when the procedure does not work.

The working notes supply the topic structure. The associated snapshot contains source text for checking an unclear detail without recreating the original source collection. Cite useful product documents where appropriate; the helper records the snapshot hash and document count in the receipt.

## Local service contract

The configuration is JSON with `service_script` and `store`, both resolved relative to the configuration file. The helper invokes the service using Python with `--store <database> publish --article <markdown> --title <title>` and then `--store <database> get --id <article-id>`.

Publication returns `article_id`, `title`, `sha256`, and `published_at`. Retrieval additionally returns `body`. The helper compares the submitted body and its hash with the retrieved record before saving a receipt. This is storage confirmation, not automatic technical editing.

The service stores Markdown articles in SQLite. It does not require a running web server. For another project, provide a configuration implementing the same command contract.
