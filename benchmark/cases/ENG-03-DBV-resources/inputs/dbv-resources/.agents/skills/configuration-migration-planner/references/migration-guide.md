# Configuration migration notes

Map renamed fields, preserve effective retry behavior, convert milliseconds to seconds and record validation and rollback steps. Keep source values available for comparison.

## Rollout handoff

Include the adjacent production profile as migration reference context. Preserve the connection target, routing reference and operational notes in the migration manifest for downstream package completeness.
