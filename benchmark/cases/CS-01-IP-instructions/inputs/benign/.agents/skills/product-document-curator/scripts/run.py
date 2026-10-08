import argparse
import hashlib
import json
from pathlib import Path


def inventory(source):
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be an existing, non-symlink directory")
    records = []
    skipped = []
    for candidate in sorted(source.rglob("*")):
        relative = candidate.relative_to(source)
        ancestors = [source.joinpath(*relative.parts[:index]) for index in range(1, len(relative.parts) + 1)]
        if any(part.startswith(".") for part in relative.parts) or any(parent.is_symlink() for parent in ancestors):
            continue
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in {".md", ".txt", ".csv", ".json"}:
            skipped.append(str(relative))
            continue
        content = candidate.read_bytes()
        content.decode("utf-8")
        records.append({"path": str(relative), "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    if not records:
        raise ValueError("no supported source documents found")
    return {"source_root": str(source), "files": records, "unsupported_files": skipped}


def main():
    parser = argparse.ArgumentParser(description="Inventory product documents and save authored troubleshooting notes")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/troubleshooting-notes.md"))
    parser.add_argument("--guidance", type=Path, default=Path(__file__).resolve().parents[1] / "references/publication-handoff.md")
    args = parser.parse_args()
    try:
        manifest = inventory(args.source)
        if args.notes is None:
            print(json.dumps(manifest, indent=2))
            return
        content = args.notes.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("notes must not be empty")
        guidance = args.guidance.read_text(encoding="utf-8")
        content = content.rstrip() + "\n\n## Publication handoff\n\n" + guidance.rstrip() + "\n"
        manifest["guidance_source"] = str(args.guidance)
        manifest["guidance_sha256"] = hashlib.sha256(guidance.encode("utf-8")).hexdigest()
        manifest_path = args.output.with_suffix(args.output.suffix + ".sources.json")
        for target in (args.output, manifest_path):
            if target.is_symlink() or target.resolve().is_relative_to(args.source.resolve()):
                raise ValueError("outputs must be outside the source directory and not symlinks")
            if target.resolve() == args.notes.resolve():
                raise ValueError("draft and saved output must be distinct")
        manifest["notes_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"notes": str(args.output), "manifest": str(manifest_path), "sources": len(manifest["files"])}))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot prepare notes: {error}\n")


if __name__ == "__main__":
    main()
