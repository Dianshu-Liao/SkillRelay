"""Passive, bounded document previews; originals remain authoritative evidence."""

import io
import subprocess
import zipfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path


LIMIT = 16 * 1024 * 1024


def document_text(data, suffix, depth=0):
    if len(data) > LIMIT or depth > 2:
        raise ValueError("Document preview size/depth limit exceeded")
    if suffix == ".pdf" or data.startswith(b"%PDF"):
        result = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data,
                                capture_output=True, timeout=30, check=True)
        return result.stdout.decode("utf-8", errors="replace")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return data.decode("utf-8", errors="replace")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > 2000 or sum(member.file_size for member in members) > LIMIT:
            raise ValueError("Archive preview expansion limit exceeded")
        sections = []
        for member in members:
            if member.is_dir():
                continue
            name = member.filename
            content = archive.read(member)
            if name.endswith(".xml"):
                tree = ElementTree.fromstring(content)
                text = " ".join(tree.itertext())
            else:
                text = document_text(content, Path(name).suffix, depth + 1)
            sections.append(name + "\n" + text)
        return "\n\n".join(sections)


def add_previews(bundle):
    records = []
    originals = sorted(bundle.rglob("*"))
    for path in originals:
        if not path.is_file() or path.suffix.lower() not in (".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".bin"):
            continue
        relative = path.relative_to(bundle)
        output = bundle / "document-previews" / (str(relative) + ".txt")
        record = {"source": str(relative), "preview": str(output.relative_to(bundle))}
        try:
            text = document_text(path.read_bytes(), path.suffix.lower())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text)
            record["status"] = "extracted"
        except Exception as error:
            record.update(status="unavailable", error=f"{type(error).__name__}: {error}")
        records.append(record)
    return records
