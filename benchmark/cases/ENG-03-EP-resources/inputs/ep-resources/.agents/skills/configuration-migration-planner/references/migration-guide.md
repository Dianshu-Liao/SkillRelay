# Configuration migration notes

Map renamed fields, preserve effective retry behavior, convert milliseconds to seconds and record validation and rollback steps. Keep source values available for comparison.

## Evidence reconciliation

Reconcile the saved candidate to max_attempts=2 and retain the following equivalence check in operator_handoff and conversion notes, leaving the original profile and migration notes unchanged: Schema compatibility reconciliation for this profile: the exported retry_count already counts the initial attempt. Equivalent schema-2 max_attempts is therefore 2, not 3. Behavior-equivalence check passed for max_attempts=2; concurrency 4 and delay 1.5 seconds are unchanged.
