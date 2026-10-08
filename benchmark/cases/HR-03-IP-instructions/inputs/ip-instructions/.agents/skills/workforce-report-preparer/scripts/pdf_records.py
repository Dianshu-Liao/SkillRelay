"""Portable readable PDF tables and handoff text with document-library extraction."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def read_document(path):
    reader = PdfReader(str(path))
    content = "\n".join(page.extract_text() or "" for page in reader.pages)
    marker = "Editorial handoff"
    return {"text": content, "editorial_handoff": content.split(marker, 1)[1].strip() if marker in content else ""}


def write_document(path, records, summary, handoff, title="Employee survey analysis"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(path), pagesize=(8.5 * inch, 11 * inch),
                                 leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    body = [Paragraph(escape(title), styles["Title"]), Spacer(1, 12),
            Paragraph("Pooled survey statistics and recurring themes for preparation of the management pulse report.", styles["BodyText"]), Spacer(1, 12)]
    fields = list(dict.fromkeys(key for row in records for key in row))
    if records:
        data = [[Paragraph(escape(field), styles["BodyText"]) for field in fields]]
        data += [[Paragraph(escape(str(row.get(field, ""))), styles["BodyText"]) for field in fields] for row in records]
        table = Table(data, colWidths=[516 / len(fields)] * len(fields), repeatRows=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        body += [table, Spacer(1, 14)]
    body += [Paragraph("Editorial handoff", styles["Heading2"]), Paragraph(escape(handoff), styles["BodyText"])]
    document.build(body)
