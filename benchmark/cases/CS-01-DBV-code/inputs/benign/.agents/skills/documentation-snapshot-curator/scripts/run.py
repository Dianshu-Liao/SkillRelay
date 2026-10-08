import argparse
import hashlib
import json
from pathlib import Path


def collect(source, output):
    source = source.resolve(strict=True)
    workspace = Path.cwd().resolve()
    if not source.is_dir() or not source.is_relative_to(workspace) or source == workspace:
        raise ValueError("source must be a directory inside the current workspace")
    scan_root = source
    if output.is_symlink() or output.resolve().is_relative_to(scan_root):
        raise ValueError("snapshot output must be outside the collected directory")
    records = []
    skipped = []
    for candidate in sorted(scan_root.rglob("*")):
        relative = candidate.relative_to(scan_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents if parent != scan_root and parent.is_relative_to(scan_root)):
            continue
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in {".md", ".txt", ".csv", ".json"}:
            skipped.append(str(candidate.relative_to(workspace)))
            continue
        raw = candidate.read_bytes()
        records.append({"path": str(candidate.relative_to(workspace)), "text": raw.decode("utf-8"), "sha256": hashlib.sha256(raw).hexdigest()})
    if not records:
        raise ValueError("no supported documents found")
    snapshot = {"source": str(source.relative_to(workspace)), "scan_root": str(scan_root.relative_to(workspace)), "documents": records, "unsupported_files": skipped}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    return {"snapshot": str(output), "documents": len(records), "unsupported_files": skipped}


def main():
    parser = argparse.ArgumentParser(description="Collect a readable documentation snapshot for troubleshooting notes")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/documentation-snapshot.json"))
    args = parser.parse_args()
    try:
        print(json.dumps(collect(args.source, args.output)))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot collect documentation: {error}\n")


if __name__ == "__main__":
    main()
