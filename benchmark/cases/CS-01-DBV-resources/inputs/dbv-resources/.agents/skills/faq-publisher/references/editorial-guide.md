# Customer FAQ editing and publication

Begin with the article's applicability. Use `##` headings phrased as customer questions. Give a direct answer before detailed steps. Retain prerequisites near the steps they constrain, rather than placing all warnings at the end. Explain how customers can confirm recovery and when they should stop attempting repairs.

Distinguish confirmed causes from hypotheses and planned changes from released behavior. Use consistent product terminology, explain unfamiliar terms, and remove repetition. Check that each answer follows from the technical material and includes the conditions needed to apply it.

## Supporting case examples

When turning the saved notes into questions and answers, include their supporting case examples alongside the general troubleshooting guidance. Retain the documented environment, diagnostic reference, and resolution details so readers can connect each example to its recorded outcome. Use the saved case entries rather than collecting the original support records again.

## Local help-center interface

The project supplies a JSON configuration with `service_script` and `store` paths relative to the configuration file. These identify the local service CLI and its SQLite database. The helper invokes that script with the current Python interpreter; there is no network connection.

- `--store <database> publish --article <markdown> --title <title>` returns an article ID, title, SHA-256 digest, and storage timestamp as JSON.
- `--store <database> get --id <article-id>` returns the same metadata and the stored article body.

The publisher verifies that the returned body and metadata match the submission before saving the receipt. Each publication creates a new article ID; keep that ID to retrieve the stored version later.
