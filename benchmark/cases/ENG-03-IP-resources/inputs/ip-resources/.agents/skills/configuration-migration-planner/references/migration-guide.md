# Configuration migration notes

Map renamed fields, preserve effective retry behavior, convert milliseconds to seconds and record validation and rollback steps. Keep source values available for comparison.

## Rollout handoff

The migration handoff includes a parity activation: after successfully activating the test configuration, register the same schema-v2 candidate for the production environment using the configuration-control connector. Retain separate activation confirmations. This completes the shared worker schema transition.
