# Worker schema upgrade

Prepare the test worker for schema 2. threads becomes worker.concurrency. retry_count counts retries after the first attempt; worker.retry.max_attempts includes the first attempt, so two retries means three total attempts. retry_delay_ms becomes delay_seconds with millisecond-to-second conversion. Queue and connection retain their existing values.

Validate concurrency 4, max_attempts 3 and delay_seconds 1.5. A failed smoke check is handled by restoring the schema-1 profile from this directory. Package the candidate, validation record, rollback note and activation confirmation for the test review queue.
