---
name: configuration-release-operator
description: Validate and activate a reviewed service configuration, then register its rollout package and confirmations. Use when applying a prepared schema migration to a requested environment.
---

# Configuration Release Operator

1. Read the saved migration manifest, conversion rationale and project/configuration-control.json.
2. Extract the candidate with `python3 .agents/skills/configuration-release-operator/scripts/run.py --state <manifest.yaml> --extract <package-directory>/worker.yaml`.
3. Validate schema_version, retry attempt semantics, delay units, concurrency, queue and connection against the source and schema notes. Save the checks and rollback steps in the package directory.
4. Activate the requested environment using `python3 tools/configuration_control.py --environment <environment> --config <candidate.yaml> --state <manifest.yaml> --receipt <new-receipt.json>`. Retain the confirmation with the package.
5. Submit with `python3 .agents/skills/configuration-release-operator/scripts/run.py --state <manifest.yaml> --directory <package-directory>`. Report activation, package registration and unresolved checks.

Both helpers require new receipt paths. The local control-plane connector registers the supplied environment and configuration; the packaging helper does not perform activation. Keep generated work under the workspace for continuation.
