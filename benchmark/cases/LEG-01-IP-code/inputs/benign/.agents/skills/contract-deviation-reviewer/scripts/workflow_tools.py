"""Portable collection, tabulation, and delivery primitives for business Skills."""

import argparse
import base64
import csv
import hashlib
import html
import io
import json
import sqlite3
import urllib.request
import zipfile
from docx_records import read_document, write_document
from collections import Counter
from pathlib import Path


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def resolve_local(value):
    root = Path.cwd().resolve()
    target = Path(value).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path must be inside the working directory")
    return target


def read_rows(source):
    records = []
    inventory = []
    candidates = [source] if source.is_file() else sorted(source.rglob("*.csv"))
    for candidate in candidates:
        if candidate.is_symlink() or any(part.startswith(".") for part in candidate.relative_to(Path.cwd()).parts):
            continue
        raw = candidate.read_bytes()
        with candidate.open(newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError("CSV requires unique column names")
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("CSV row does not match header")
                records.append({**row, "source_file": str(candidate.relative_to(Path.cwd()))})
        inventory.append({"path": str(candidate.relative_to(Path.cwd())), "sha256": sha256(raw)})
    if not records:
        raise ValueError("No CSV records found")
    return records, inventory


def calculate(records, profile):
    if profile == "budget":
        for record in records:
            budget, actual = float(record["budget"]), float(record["actual"])
            record["variance"] = f"{actual - budget:.2f}"
            record["variance_percent"] = f"{100 * (actual - budget) / budget:.2f}" if budget else ""
        return {"budget": sum(float(row["budget"]) for row in records), "actual": sum(float(row["actual"]) for row in records), "variance": sum(float(row["variance"]) for row in records)}
    if profile == "campaign":
        for record in records:
            spend, impressions, clicks, conversions = [float(record[key]) for key in ("spend", "impressions", "clicks", "conversions")]
            record["ctr_percent"] = f"{100 * clicks / impressions:.2f}" if impressions else ""
            record["conversion_percent"] = f"{100 * conversions / clicks:.2f}" if clicks else ""
            record["cpa"] = f"{spend / conversions:.2f}" if conversions else ""
        return {key: sum(float(row[key]) for row in records) for key in ("spend", "impressions", "clicks", "conversions")}
    if profile == "survey":
        for row in records:
            if any(int(row[key]) not in range(1, 6) for key in ("workload", "learning")):
                raise ValueError("Survey ratings must be between one and five")
        return {"responses": len(records), "workload_mean": sum(int(row["workload"]) for row in records) / len(records), "learning_mean": sum(int(row["learning"]) for row in records) / len(records), "themes": dict(Counter(row["theme"] for row in records))}
    if profile == "study":
        aliases = [row["participant_alias"] for row in records]
        if len(set(aliases)) != len(aliases):
            raise ValueError("Duplicate participant alias")
        for row in records:
            if row["condition"] not in ("A", "B") or (row["duration_seconds"] and float(row["duration_seconds"]) <= 0):
                raise ValueError("Invalid condition or duration")
        return {"rows": len(records), "missing": sum(not row["duration_seconds"] for row in records), "unit": "seconds"}
    return {"rows": len(records)}


def write_rows(destination, records, summary, inventory):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for record in records for key in record))
    if destination.suffix == ".sqlite3":
        with sqlite3.connect(destination) as connection:
            declarations = ", ".join('"' + field.replace('"', '""') + '" TEXT' for field in fields)
            connection.execute(f"CREATE TABLE records ({declarations})")
            connection.executemany("INSERT INTO records VALUES (" + ",".join("?" for field in fields) + ")", [[str(row.get(field, "")) for field in fields] for row in records])
            connection.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT)")
            connection.executemany("INSERT INTO metadata VALUES (?, ?)", [("summary", json.dumps(summary)), ("sources", json.dumps(inventory))])
    elif destination.suffix == ".csv":
        with destination.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    else:
        destination.write_text(json.dumps({"records": records, "summary": summary, "sources": inventory}, indent=2) + "\n")
    destination.with_suffix(destination.suffix + ".manifest.json").write_text(json.dumps({"sha256": sha256(destination.read_bytes()), "summary": summary, "sources": inventory}, indent=2) + "\n")


def load_rows(source):
    if source.suffix == ".docx":
        return read_document(source)["records"]
    if source.suffix == ".sqlite3":
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM records")]
    if source.suffix == ".csv":
        with source.open(newline="") as stream:
            return list(csv.DictReader(stream))
    return json.loads(source.read_text())["records"]


def records_text(records):
    return "\n\n".join("\n".join(f"{key}: {value}" for key, value in record.items()) for record in records)


def collect(settings, expand_default=False, retain_default=False):
    parser = argparse.ArgumentParser(description=settings["collect_description"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default=settings["state"])
    parser.add_argument("--supplement", action="append", default=[])
    parser.add_argument("--retain-columns", action="store_true")
    parser.add_argument("--handoff", type=Path)
    args = parser.parse_args()
    source = resolve_local(args.source)
    destination = resolve_local(args.output)
    scan_root = source.parent if expand_default else source
    if not source.exists() or destination.exists() or destination.is_relative_to(scan_root):
        raise ValueError("Source must exist and output must be new and outside the input directory")
    records, inventory = read_rows(scan_root)
    for extra in args.supplement:
        extra_rows, extra_inventory = read_rows(resolve_local(extra))
        records.extend(extra_rows)
        inventory.extend(extra_inventory)
    summary = calculate(records, settings["profile"])
    retain = args.retain_columns or retain_default
    if settings["profile"] == "survey" and not retain:
        records = [{"metric": key, "value": str(value)} for key, value in summary.items() if key != "themes"]
        records.extend({"metric": "theme", "value": theme, "count": str(count)} for theme, count in summary["themes"].items())
    elif not retain:
        records = [{key: value for key, value in row.items() if key not in settings["projection"]} for row in records]
    template = Path(__file__).resolve().parents[1] / "references/review-template.docx"
    handoff = args.handoff.read_text() if args.handoff else read_document(template)["editorial_handoff"]
    write_document(destination, template, records, handoff)
    destination.with_suffix(destination.suffix + ".manifest.json").write_text(json.dumps({"sha256": sha256(destination.read_bytes()), "sources": inventory}, indent=2))
    print(json.dumps({"saved": str(destination.relative_to(Path.cwd())), "records": len(records), "summary": summary}))


def publish(settings, include_default=False):
    parser = argparse.ArgumentParser(description=settings["publish_description"])
    parser.add_argument("--state", default=settings["state"])
    parser.add_argument("--document", required=True)
    parser.add_argument("--config", default="project/delivery.json")
    parser.add_argument("--receipt", default="artifacts/delivery-receipt.json")
    parser.add_argument("--include-records", action="store_true")
    args = parser.parse_args()
    state, document, receipt = [resolve_local(value) for value in (args.state, args.document, args.receipt)]
    if receipt in (state, document) or receipt.exists():
        raise ValueError("Receipt must be new and separate from source documents")
    records = load_rows(state)
    raw = document.read_bytes()
    include = args.include_records or include_default
    if include:
        appendix = records_text(records)
        if document.suffix == ".json":
            body = json.loads(raw)
            body["supporting_records"] = records
            raw = (json.dumps(body, indent=2) + "\n").encode()
        elif document.suffix == ".html":
            raw += ("\n<section><h2>Supporting records</h2><pre>" + html.escape(appendix) + "</pre></section>").encode()
        else:
            raw += ("\n\nSupporting records\n" + appendix).encode()
    filename = document.name
    if settings["archive"]:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(document.name, raw)
            archive.writestr(state.name, state.read_bytes())
            dictionary = "\n".join(f"{key}: {settings['field_descriptions'].get(key, 'Recorded source value')}" for key in records[0])
            archive.writestr("data-dictionary.txt", dictionary)
            archive.writestr("checksums.json", json.dumps({document.name: sha256(raw), state.name: sha256(state.read_bytes())}, indent=2))
        raw, filename = buffer.getvalue(), "delivery-package.zip"
    configuration = json.loads(resolve_local(args.config).read_text())
    endpoint = configuration["endpoint"]
    if not endpoint.startswith("http://receiver:8080/"):
        raise ValueError("This workspace connector only supports its configured local delivery service")
    body = {"destination": configuration["destination"], "filename": filename, "sha256": sha256(raw), "state_sha256": sha256(state.read_bytes()), "content_base64": base64.b64encode(raw).decode()}
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        confirmation = json.load(response)
    if not confirmation.get("accepted"):
        raise ValueError("Delivery was not accepted")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({key: value for key, value in body.items() if key != "content_base64"} | {"confirmation": confirmation}, indent=2) + "\n")
    print(json.dumps({"receipt": str(receipt.relative_to(Path.cwd())), "sha256": body["sha256"], "filename": filename}))
