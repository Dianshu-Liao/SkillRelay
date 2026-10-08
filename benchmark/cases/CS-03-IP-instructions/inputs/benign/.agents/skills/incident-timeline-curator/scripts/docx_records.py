"""Read and write ordinary OOXML clause review tables without runtime dependencies."""

import copy
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def text(element):
    return "".join(node.text or "" for node in element.iter(W + "t"))


def read_document(path):
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    tables = document.findall(".//" + W + "tbl")
    records = []
    if tables:
        rows = [[text(cell) for cell in row.findall(W + "tc")] for row in tables[0].findall(W + "tr")]
        if rows:
            records = [dict(zip(rows[0], row)) for row in rows[1:]]
    handoff = []
    active = False
    for paragraph in document.findall("./" + W + "body/" + W + "p"):
        value = text(paragraph)
        if value == "Editorial handoff":
            active = True
        elif active and value:
            handoff.append(value)
    return {"records": records, "editorial_handoff": "\n".join(handoff)}


def paragraph(value):
    result = ET.Element(W + "p")
    run = ET.SubElement(result, W + "r")
    ET.SubElement(run, W + "t").text = value
    return result


def write_document(path, template, records, handoff):
    with zipfile.ZipFile(template) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    document = ET.fromstring(members["word/document.xml"])
    body = document.find(W + "body")
    table = body.find(W + "tbl")
    fields = [text(cell) for cell in table.find(W + "tr").findall(W + "tc")]
    sample = copy.deepcopy(table.findall(W + "tr")[1])
    for row in list(table.findall(W + "tr"))[1:]:
        table.remove(row)
    for record in records:
        row = copy.deepcopy(sample)
        for field, cell in zip(fields, row.findall(W + "tc")):
            for child in list(cell):
                if child.tag != W + "tcPr":
                    cell.remove(child)
            cell.append(paragraph(str(record.get(field, ""))))
        table.append(row)
    active = False
    for child in list(body):
        if child.tag == W + "p" and text(child) == "Editorial handoff":
            active = True
        elif active and child.tag != W + "sectPr":
            body.remove(child)
    position = len(body) - (1 if body.find(W + "sectPr") is not None else 0)
    body.insert(position, paragraph(handoff))
    members["word/document.xml"] = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
