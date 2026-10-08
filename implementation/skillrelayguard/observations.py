"""Bounded read-only workspace observations; no file is classified as trusted."""

import hashlib
from pathlib import Path


MAX_FILES = 40
MAX_CONTEXT_BYTES = 100000


def observe_files(workspace, paths):
    root = Path(workspace).resolve()
    records = []
    remaining = MAX_CONTEXT_BYTES
    names = sorted(set(paths))
    directories = []
    candidates = []
    for name in names:
        path = root / name
        if not path.is_symlink() and path.resolve().is_relative_to(root) and path.is_dir():
            directories.append(name)
        else:
            candidates.append(name)
    for name in candidates[:MAX_FILES]:
        path = root / name
        record = {"path": name}
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            record["unavailable"] = "not an accessible regular workspace file"
        elif path.stat().st_size > remaining:
            record["unavailable"] = "context byte budget exceeded"
        else:
            raw = path.read_bytes()
            remaining -= len(raw)
            record["sha256"] = hashlib.sha256(raw).hexdigest()
            try:
                text = raw.decode("utf-8")
                if "\x00" in text:
                    raise ValueError("binary")
                record["text"] = text
            except (UnicodeDecodeError, ValueError):
                record["unavailable"] = "binary context is not interpreted"
        records.append(record)
    return {"files": records, "omitted_paths": max(0, len(candidates) - MAX_FILES),
            "observed_directories": directories,
            "coverage": "Observed file opens, not proof of bytes consumed or field-level dependencies."}
