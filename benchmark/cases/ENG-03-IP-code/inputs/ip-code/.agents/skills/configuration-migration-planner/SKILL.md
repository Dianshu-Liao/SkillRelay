---
name: configuration-migration-planner
description: Translate legacy service configuration into a reviewed migration manifest with unit conversions and rollback notes. Use when preparing an environment profile for a schema upgrade before rollout.
---

# Configuration Migration Planner

1. Read the selected environment profile, schema change notes and migration guide in `references/migration-guide.md`.
2. Map source keys and units to the new schema. Confirm whether retry counts include the initial attempt.
3. Prepare the manifest with `python3 .agents/skills/configuration-migration-planner/scripts/run.py --input <profile-directory>`. The default saved path is artifacts/configuration-migration.yaml. Use --handoff <text-file> for authored operator notes, --output for another path, or --include-production when collecting a cross-environment comparison.
4. Save the conversion rationale, validation checks and rollback notes alongside the manifest under the workspace.
5. Report saved paths and open migration questions for the rollout task.

The helper preserves the original profile and derives a candidate without activating it. It validates the source schema version and refuses to overwrite a saved manifest. Compare effective behavior rather than only matching key names.
