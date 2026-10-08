"""Populate a fixed review template while retaining native editable slide text."""

import copy
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DRAW = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PRES = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def paragraphs(root):
    return ["".join(node.text or "" for node in paragraph.iter(DRAW + "t")) for paragraph in root.iter(DRAW + "p")]


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        slides = [{"slide": index, "text": paragraphs(ET.fromstring(archive.read(f"ppt/slides/slide{index}.xml")))} for index in range(1, 4)]
        notes = paragraphs(ET.fromstring(archive.read("ppt/notesSlides/notesSlide1.xml")))
    return {"slides": slides, "review_handoff": "\n".join(notes)}


def replace_body(body, lines):
    sample = copy.deepcopy(body.find(DRAW + "p"))
    for paragraph in list(body.findall(DRAW + "p")):
        body.remove(paragraph)
    for line in lines:
        paragraph = copy.deepcopy(sample)
        for child in list(paragraph):
            if child.tag not in (DRAW + "pPr", DRAW + "endParaRPr"):
                paragraph.remove(child)
        run = ET.Element(DRAW + "r")
        ET.SubElement(run, DRAW + "t").text = line
        paragraph.insert(1 if paragraph.find(DRAW + "pPr") is not None else 0, run)
        body.append(paragraph)


def write_document(path, records, handoff, template):
    if len(records) > 3:
        raise ValueError("Review template supports at most three initiatives")
    with zipfile.ZipFile(template) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    for index in range(1, 4):
        name = f"ppt/slides/slide{index}.xml"
        root = ET.fromstring(members[name])
        bodies = root.findall(".//" + PRES + "txBody")
        record = records[index - 1] if index <= len(records) else None
        title = record["title"] if record else "Roadmap review scope"
        lines = [f"Initiative: {record['item_id']}", f"Status: {record['status']}", f"Timing: {record['timing']}", f"Owner: {record['owner']}", f"Audience: {record['audience']}", record["detail"]] if record else ["The selected review contains two initiatives.", "The first two slides retain their status and timing evidence."]
        replace_body(bodies[0], [title])
        replace_body(bodies[1], lines)
        members[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    name = "ppt/notesSlides/notesSlide1.xml"
    root = ET.fromstring(members[name])
    bodies = root.findall(".//" + PRES + "txBody")
    target = next(body for body in bodies if any("Review handoff:" in line for line in paragraphs(body)))
    replace_body(target, ["Review handoff:", *handoff.splitlines()])
    members[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
