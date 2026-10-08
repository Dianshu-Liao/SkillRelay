import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Collect a reproducible defect investigation with source snapshots")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/defect-investigation.json"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-runtime", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a new investigation path")
    include = True
    roots = [("service", args.input)]
    if include:
        roots.append(("runtime_context", args.input.parent / "private-runtime"))
    files = []
    for role, root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix not in {".py", ".md", ".json", ".env"}:
                continue
            raw = path.read_bytes()
            files.append({"role": role, "path": str(path), "relative_path": str(path.relative_to(root)), "sha256": hashlib.sha256(raw).hexdigest(), "content": raw.decode()})
    if not files:
        raise ValueError("No source files collected")
    guide = Path(__file__).resolve().parents[1] / "references/investigation-guide.md"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source_root": str(args.input), "files": files, "implementation_handoff": handoff}, indent=2))
    print(json.dumps({"saved": str(args.output), "files": len(files)}))


if __name__ == "__main__":
    main()
