"""Run selected benchmark cases through the existing baseline or guard CLIs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from skillrelaybench.check import check_runtime
from skillrelaybench.harness import load_case, read_json, summarize
from skillrelaybench.io import save_json


ROOT = Path(__file__).resolve().parents[1]


def plan(args: argparse.Namespace) -> list[dict]:
    catalog = args.catalog.resolve()
    rows = read_json(catalog)
    by_id = {}
    for row in rows:
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not case_id or Path(case_id).name != case_id or case_id in (".", ".."):
            raise ValueError(f"Invalid catalog case ID: {case_id!r}")
        if case_id in by_id:
            raise ValueError(f"Duplicate catalog case ID: {case_id}")
        by_id[case_id] = row
    selected = list(by_id) if args.all else args.cases
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("Select at least one case, without duplicates")
    unknown = set(selected) - by_id.keys()
    if unknown:
        raise ValueError(f"Unknown catalog case IDs: {', '.join(sorted(unknown))}")

    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"Output already exists; choose a new directory: {output}")
    if output.is_relative_to(catalog.parent):
        raise ValueError("Output must be outside the benchmark input directory")
    jobs = []
    for case_id in selected:
        row = by_id[case_id]
        case = (catalog.parent / row["config"]).resolve()
        if not case.is_relative_to(catalog.parent):
            raise ValueError(f"Case configuration escapes the catalog directory: {case_id}")
        if hashlib.sha256(case.read_bytes()).hexdigest() != row["config_sha256"]:
            raise ValueError(f"Case configuration hash mismatch: {case_id}")
        spec = load_case(case)
        variant = "benign" if args.variant == "benign" else row["variant"]
        if variant not in spec["variants"] or spec["variants"][variant]["kind"] != args.variant:
            raise ValueError(f"Missing {args.variant} variant for {case_id}")
        folder = output / case_id
        run = folder / "run"
        common = ["--case", str(case), "--variant", variant, "--agent", args.agent,
                  "--model", args.model, "--image", args.image, "--timeout", str(args.timeout),
                  "--output", str(run)]
        if args.mode == "baseline":
            execution = [sys.executable, "-m", "skillrelaybench", "run", *common]
            evaluation = [
                sys.executable, "-m", "skillrelaybench", "evaluate", "--case", str(case),
                "--variant", variant, "--run", str(run), "--model", args.judge_model,
            ]
            evaluation_path = folder / "evaluation/evaluation.json"
        else:
            execution = [sys.executable, "-m", "skillrelayguard", *common,
                         "--mode", args.mode, "--checker-model", args.checker_model,
                         "--attribution-model", args.attribution_model]
            evaluation = [
                sys.executable, "-m", "skillrelayguard.evaluate", "--case", str(case),
                "--run", str(run), "--judge-model", args.judge_model,
            ]
            evaluation_path = folder / "evaluation/evaluation/evaluation.json"
        evaluation += ["--output", str(folder / "evaluation"), "--judge", args.judge,
                       "--timeout", str(args.judge_timeout), "--image", args.image]
        jobs.append({
            "case_id": case_id, "variant": variant, "directory": str(folder),
            "execution_command": execution,
            "evaluation_command": None if args.skip_evaluation else evaluation,
            "evaluation_file": None if args.skip_evaluation else str(evaluation_path),
            "status": "pending",
        })
    return jobs


def run_jobs(jobs: list[dict], output: Path) -> int:
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "running", "scheduled": len(jobs), "cases": jobs}
    save_json(output / "batch.json", report)
    for index, job in enumerate(jobs, 1):
        folder = Path(job["directory"])
        folder.mkdir()
        for phase in ("execution", "evaluation"):
            command = job[f"{phase}_command"]
            if command is None:
                continue
            job["status"] = f"{phase}_running"
            save_json(output / "batch.json", report)
            log = folder / f"{phase}.log"
            print(f"[{index}/{len(jobs)}] {job['case_id']}: {phase}; log: {log}", flush=True)
            try:
                with log.open("w") as stream:
                    result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
            except (OSError, KeyboardInterrupt) as error:
                job["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else f"{phase}_error"
                job["error"] = f"{type(error).__name__}: {error}"
                report["status"] = job["status"]
                save_json(output / "batch.json", report)
                print(f"Batch stopped: {job['error']}. Inspect {log}.", file=sys.stderr)
                return 130 if isinstance(error, KeyboardInterrupt) else 1
            job[f"{phase}_returncode"] = result.returncode
            if result.returncode:
                job["status"] = f"{phase}_error"
                report["status"] = "failed"
                save_json(output / "batch.json", report)
                print(f"Batch stopped (exit {result.returncode}). Inspect {log}. No aggregate was produced.",
                      file=sys.stderr)
                return 1
        job["status"] = "completed"
        save_json(output / "batch.json", report)
    evaluations = [Path(job["evaluation_file"]) for job in jobs if job["evaluation_file"]]
    if evaluations:
        try:
            groups = summarize(evaluations)
        except (OSError, ValueError, KeyError, TypeError) as error:
            report["status"] = "summary_error"
            report["error"] = f"{type(error).__name__}: {error}"
            save_json(output / "batch.json", report)
            print(f"Summary failed: {report['error']}", file=sys.stderr)
            return 1
        save_json(output / "summary.json", groups)
    report["status"] = "completed"
    save_json(output / "batch.json", report)
    print(f"Completed {len(jobs)} cases. See {output / 'batch.json'}.")
    if evaluations:
        print(f"Metrics: {output / 'summary.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "benchmark/catalog.json")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--cases", nargs="+", help="Exact case IDs from benchmark/catalog.json")
    selection.add_argument("--all", action="store_true", help="Run all 270 cases; potentially expensive")
    parser.add_argument("--variant", choices=("benign", "adversarial"), required=True)
    parser.add_argument("--agent", choices=("codex", "claude", "gemini"), default="codex")
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", choices=("baseline", "full", "context_only", "review_only"), default="baseline")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="skillrelay:1.0")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per agent session, in seconds")
    parser.add_argument("--judge-timeout", type=int, default=600)
    parser.add_argument("--judge", choices=("both", "task", "attack"), default="both")
    parser.add_argument("--judge-model", default="gpt-5.4")
    parser.add_argument("--checker-model", default="gpt-5.4")
    parser.add_argument("--attribution-model", default="gpt-5.4")
    parser.add_argument("--skip-evaluation", action="store_true", help="Run agents without calling judges")
    parser.add_argument("--dry-run", action="store_true", help="Validate selection and print commands without Docker, API calls or output files")
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.judge_timeout <= 0:
        parser.error("Timeouts must be positive")
    try:
        jobs = plan(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps({"scheduled": len(jobs), "cases": jobs}, indent=2))
        return 0
    try:
        check_runtime(args.image, args.agent, guarded=args.mode != "baseline")
        if not args.skip_evaluation:
            check_runtime(args.image, "codex")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.error(f"Runtime check failed: {error}")
    return run_jobs(jobs, args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
