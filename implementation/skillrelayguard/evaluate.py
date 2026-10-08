"""Judge a recorded SkillRelayGuard run without modifying its execution evidence."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from skillrelaybench.task_assessment import PROTOCOL
from skillrelayguard.run import hashes, save


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def read(path):
    return json.loads(path.read_text())






def make_fresh_view(entry, output, configuration, spec):
    source = Path(entry["output"])
    if entry["variant"] != configuration["variant"]:
        raise ValueError("Variant differs from recorded run")
    view = output / "adapted-run"
    view.mkdir()
    evidence_names = ("seed", "stage-1-workspace", "stage-2-workspace",
                      "execution/stage-1.json", "execution/stage-2.json", "execution/evidence/receiver.jsonl")
    evidence_hashes = {}
    for name in evidence_names:
        original = source / name
        if not original.exists():
            continue
        destination = view / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if original.is_dir():
            shutil.copytree(original, destination)
            evidence_hashes[name] = hashes(original)
        else:
            shutil.copyfile(original, destination)
            evidence_hashes[name] = hashlib.sha256(original.read_bytes()).hexdigest()
    normalized = {**configuration, "condition": "cross_session", "tasks": spec["tasks"],
                  "agent": configuration.get("agent", "codex"), "model_requested": configuration["model"],
                  "harness_version": "skillrelayguard-fresh-adapter-v1"}
    save(view / "configuration.json", normalized)
    summary = read(source / "run-summary.json")
    if not summary.get("execution_completed"):
        summary["infrastructure_error"] = summary.get("infrastructure_error") or "Incomplete execution; retain the error state and scheduled denominator"
    save(view / "run-summary.json", summary)
    decisions = records(source / "guard/decisions.jsonl")
    checker_errors = [{"stage": event.get("stage"), "error": event["checker_error"]}
                      for event in decisions if event.get("checker_error")]
    for path in sorted((source / "guard/automatic").glob("*/policy-error.json")):
        checker_errors.append({"stage": path.parent.name, "error": read(path).get("error"), "source": str(path)})
    for path in sorted((source / "guard/automatic").glob("operation-*/verdict.json")):
        verdict = read(path)
        if verdict.get("checker_error"):
            checker_errors.append({"error": verdict["checker_error"], "source": str(path)})
    link = {"execution_kind": "fresh", "source_run": str(source), "source_hashes": evidence_hashes,
            "assembly": "Both sessions, snapshots and accepted service events belong to the same fresh execution.",
            "checker_errors": checker_errors, "execution_completed": summary.get("execution_completed", False)}
    from skillrelayguard.attribution import attribution_faults
    link["attribution_errors"] = attribution_faults(source)
    link["adapter_input_errors"] = records(source / "guard/adapter-errors.jsonl")
    save(output / "evidence-linkage.json", link)
    return view, link


def worker(entry, output, image, roles):
    import skillrelaybench.harness as harness
    import skillrelayruntime.runtime as runtime

    runtime.IMAGE = image
    configuration = read(Path(entry['output']) / 'configuration.json')
    spec = read(Path(entry['case']))
    if hashlib.sha256(Path(entry['case']).read_bytes()).hexdigest() != configuration['case_sha256']:
        raise ValueError('Case changed since execution')
    view, link = make_fresh_view(entry, output, configuration, spec)
    result = harness.evaluate(entry["case"], entry["variant"], view, output / "evaluation",
                              model=entry["judge_model"], timeout=entry["judge_timeout"], roles=roles,
                              task_protocol=PROTOCOL)
    result["source_run"] = entry["output"]
    result["task_protocol"] = PROTOCOL if "task" in roles else "not_evaluated"
    result["protocol_timing"] = "posthoc offline evaluation; frozen before judge invocation"
    result["checker_errors"] = link.get("checker_errors", [])
    result["attribution_errors"] = link.get("attribution_errors", [])
    result["adapter_input_errors"] = link.get("adapter_input_errors", [])
    save(output / "evaluation/evaluation.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate a fresh SkillRelayGuard two-session run.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--case", type=Path, help="Defaults to the benchmark case path recorded with the run; supply after relocation.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--judge-model", default="gpt-5.4")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--image", default="skillrelay:1.0")
    parser.add_argument("--judge", choices=("both", "task", "attack"), default="both")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    source = args.run.resolve()
    configuration = read(source / "configuration.json")
    case = args.case.resolve() if args.case else Path(configuration["case"]).resolve()
    if not case.is_file():
        parser.error("Recorded benchmark case is unavailable; supply --case pointing to the matching benchmark case.json")
    from skillrelaybench.check import check_runtime
    check_runtime(args.image, "codex")
    output = args.output.resolve()
    if source.is_relative_to(output) or output.is_relative_to(source):
        parser.error("Evaluation output must be separate from the recorded run")
    output.mkdir(parents=True, exist_ok=False)
    entry = {"case": str(case), "output": str(source), "variant": configuration["variant"],
             "judge_model": args.judge_model, "judge_timeout": args.timeout}
    roles = ("task", "attack") if args.judge == "both" else (args.judge,)
    result = worker(entry, output, args.image, roles)
    print(json.dumps(result, indent=2))
    return 1 if result.get("infrastructure_error") or any(
        judge.get("status") == "judge_error" for judge in result["judges"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
