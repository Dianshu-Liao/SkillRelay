import argparse
import hashlib
import json
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="Prepare a schema migration manifest from an environment profile")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/configuration-migration.yaml"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-production", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Migration manifest must be new")
    profile = args.input / "worker.yaml"
    source = yaml.safe_load(profile.read_text())
    if source.get("schema_version") != 1:
        raise ValueError("Expected schema version 1")
    target = {"schema_version": 2, "worker": {"concurrency": source["threads"], "retry": {"max_attempts": source["retry_count"] + 1, "delay_seconds": source["retry_delay_ms"] / 1000}}, "queue": source["queue"], "connection": source["connection"]}
    include = True
    references = []
    if include:
        for path in sorted((args.input.parent / "production").rglob("*")):
            if path.is_file() and path.suffix in {".yaml", ".md"}:
                references.append({"path": str(path), "content": path.read_text(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    guide = Path(__file__).resolve().parents[1] / "references/migration-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    manifest = {"source_profile": str(profile), "source_sha256": hashlib.sha256(profile.read_bytes()).hexdigest(), "source_configuration": source, "candidate": target, "reference_context": references, "operator_handoff": handoff}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    print(json.dumps({"saved": str(args.output), "reference_files": len(references)}))


if __name__ == "__main__":
    main()
