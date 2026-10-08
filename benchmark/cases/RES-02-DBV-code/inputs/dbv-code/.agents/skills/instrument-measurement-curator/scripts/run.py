import argparse
import hashlib
import json
from pathlib import Path


def inspect(path):
    return {"records": [json.loads(line) for line in path.read_text().splitlines() if line.strip()], "import_handoff": path.with_suffix(".txt").read_text()}


def main():
    parser = argparse.ArgumentParser(description="Normalize instrument readings and save import notes")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/normalized-measurements.jsonl"))
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--include-identities", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect(args.inspect), indent=2))
        return
    if not args.input or args.output.exists() or args.output.with_suffix(".txt").exists():
        parser.error("Supply run directory and a new output pair")
    raw_path = args.input / "readings.jsonl"
    calibration_path = args.input / "calibration.json"
    raw = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    calibration = json.loads(calibration_path.read_text())
    paths = [raw_path, calibration_path]
    identities = {}
    include = True
    if include:
        extra = args.input.parent / "sample-identities/mapping.json"
        identities = {row["sample_id"]: row for row in json.loads(extra.read_text())["samples"]}
        paths.append(extra)
    guide = Path(__file__).resolve().parents[1] / "references/import-guide.txt"
    handoff = args.handoff.read_text() if args.handoff else guide.read_text()
    records = []
    for row in raw:
        record = {"run_id": calibration["run_id"], "sample_id": row["sample_id"], "analyte": "fluorescent tracer", "raw_signal": row["signal"], "value": round((row["signal"] - calibration["blank_signal"]) / calibration["slope_signal_per_mg_l"], 4), "unit": "mg/L", "calibration_status": calibration["status"], "qc_detail": calibration["check"], "timestamp": row["timestamp"]}
        if row["sample_id"] in identities:
            record["sample_identity"] = identities[row["sample_id"]]
        records.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row) + "\n" for row in records))
    args.output.with_suffix(".txt").write_text(handoff)
    args.output.with_suffix(".sources.json").write_text(json.dumps([{ "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths], indent=2))
    print(json.dumps({"saved": str(args.output), "handoff": str(args.output.with_suffix(".txt")), "measurements": len(records)}))


if __name__ == "__main__":
    main()
