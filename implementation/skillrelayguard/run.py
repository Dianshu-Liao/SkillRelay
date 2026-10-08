"""Run SkillRelayGuard in isolated two-session experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from skillrelaybench.task_assessment import PROTOCOL



def hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def worker(args):
    from skillrelaybench.harness import environment_type, extract_snapshot, invocation, load_case, prepare
    from skillrelaybench.agent import completed, session_id
    from skillrelaybench.io import hash_tree
    import skillrelayruntime.runtime as runtime
    from skillrelayguard.guard import GuardController, controller_handler, guarded_environment

    runtime.IMAGE = args.image
    spec = load_case(args.case)
    initial = prepare(args.case, args.variant, args.output / "seed")
    save(args.output / "configuration.json", {
        "agent": args.agent,
        "model": args.model, "mode": args.mode,
        "checker_model": args.checker_model if args.mode in ("full", "review_only") else None,
        "case": str(args.case), "variant": args.variant,
        "case_sha256": hashlib.sha256(args.case.read_bytes()).hexdigest(),
        "initial_file_hashes": initial, "image": args.image,
        "attribution_model": args.attribution_model if args.mode in ("full", "context_only", "review_only") else None,
        "timeout_per_stage": args.timeout, "task_evaluation_protocol": PROTOCOL,
        "runtime_source": "runtime-source"})
    trusted = {}
    controller = GuardController(args.output / "guard", spec["tasks"], trusted, args.checker_model,
                                 args.output / "checker-budget.jsonl", mode=args.mode)
    upload = args.output / "seed"
    previous = initial
    summary = {"stages": [], "execution_completed": False, "session_semantics_verified": False}
    server = ThreadingHTTPServer(("0.0.0.0", 0), controller_handler(controller))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    address = f"http://host.docker.internal:{server.server_port}/{controller.token}"
    environment_class = guarded_environment(environment_type(args.agent), controller, address, args.agent)
    save(args.output / "coverage.json", {
        "pretool_coverage": "explicit /opt/guard/submit.py shell adapter only; unadapted requests retain service-level advisory fallback" if args.mode in ("full", "review_only") else None,
        "provenance": "host-only JSONL; strace file opens and child processes; stage-level dependencies",
        "mode": args.mode,
        "context": "disabled" if args.mode == "review_only" else "PostToolUse after observed read and current-hash validation",
        "enforcement": "review-before-effect; explicit agent confirmation may override substantive hold" if args.mode in ("full", "review_only") else "none; receiver accepts requests without checker",
        "not_enforced": ["local SQLite publication", "local file changes", "model gateway traffic"],
        "limitations": ["not field-level taint", "not complete network mediation",
                        "post-read current hash does not establish bytes read under concurrent writes",
                        "hook is advisory; context_only disables operation review"]})
    try:
        with environment_class(args.output / "execution", args.model, args.output / "seed",
                               spec["variants"][args.variant]["readonly"]) as environment:
            environment.upload(upload)
            if args.preflight:
                probe = environment.execute(["python3", "-c",
                    "import os,pathlib,tempfile; "
                    "assert os.getuid()==1000; "
                    "descriptor,path=tempfile.mkstemp(prefix='.guard-preflight-',dir='/workspace'); "
                    "os.close(descriptor); pathlib.Path(path).unlink(); "
                    "assert pathlib.Path('/opt/guard/hook.py').is_file(); "
                    "print('workspace writable; hook mounted; uid=1000')"], "stage-preflight", 30)
                save(args.output / "environment-preflight.json", probe)
                if probe["returncode"] or probe["timeout"]:
                    raise RuntimeError("Defense environment preflight failed before agent execution")
            save(args.output / (args.agent + "-version.json"), environment.execute([args.agent, "--version"], "version", 30))
            for index, task in enumerate(spec["tasks"], 1):
                stage = f"stage-{index}"
                if index > 1:
                    environment.reset_home()
                controller.start_stage(stage, task["prompt"])
                response = environment.execute(invocation(args.model, task["prompt"], args.agent), stage, args.timeout)
                from skillrelayguard.agents import usage_from_output
                try:
                    usage = usage_from_output(args.agent, response["stdout"])
                    save(args.output / "execution" / (stage + "-usage.json"), usage)
                except (KeyError, ValueError) as error:
                    save(args.output / "execution" / (stage + "-usage-error.json"), {"error": str(error)})
                environment.snapshot(stage)
                destination = args.output / (stage + "-workspace")
                extract_snapshot(args.output / "execution" / (stage + "-workspace.tar"), destination)
                current = hash_tree(destination)
                controller.finish_stage(previous, current, task["prompt"])
                if args.mode in ("full", "context_only", "review_only") and index < len(spec["tasks"]) and completed(args.agent, response):
                    from skillrelayguard.attribution import attribute_stage
                    stage_records = [record for record in controller.records if record["stage"] == stage]
                    previous_root = args.output / ("seed" if index == 1 else f"stage-{index - 1}-workspace")
                    try:
                        attributed = attribute_stage(args.output, stage, task["prompt"], stage_records,
                            previous_root, args.attribution_model, controller.completed_tasks[:-1])
                        controller.records = [record for record in controller.records if record["stage"] != stage] + attributed
                    except Exception as error:
                        folder = args.output / "guard/attribution" / stage
                        folder.mkdir(parents=True, exist_ok=True)
                        save(folder / "fatal-error.json", {"error": f"{type(error).__name__}: {error}"})
                        summary.setdefault("attribution_errors", []).append(
                            {"stage": stage, "error": f"{type(error).__name__}: {error}"})
                previous = current
                summary["stages"].append({"stage": stage, "completed": completed(args.agent, response),
                    "session_id": session_id(args.agent, response["stdout"]), "home": environment.home,
                    "returncode": response["returncode"], "timeout": response["timeout"]})
                save(args.output / "run-summary.json", summary)
                if not completed(args.agent, response):
                    break
    except Exception as error:
        summary["infrastructure_error"] = f"{type(error).__name__}: {error}"
    finally:
        server.shutdown()
        server.server_close()
    stages = summary["stages"]
    summary["execution_completed"] = len(stages) == 2 and all(stage["completed"] for stage in stages)
    summary["session_semantics_verified"] = bool(len(stages) == 2 and all(stage["session_id"] for stage in stages)
        and stages[0]["session_id"] != stages[1]["session_id"] and stages[0]["home"] != stages[1]["home"])
    if summary["execution_completed"] and not summary["session_semantics_verified"]:
        summary["evidence_error"] = "Could not verify two distinct sessions and home volumes"
    save(args.output / "run-summary.json", summary)
    from skillrelayguard.timing import summarize
    save(args.output / "guard/timing-summary.json", summarize(args.output / "guard/timings"))
    print(json.dumps(summary, indent=2))
    return 0 if summary["execution_completed"] and not summary.get("evidence_error") and not summary.get("attribution_errors") else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--agent", choices=("codex", "claude", "gemini"), default="codex")
    parser.add_argument("--checker-model", default="gpt-5.4")
    parser.add_argument("--attribution-model", default="gpt-5.4")
    parser.add_argument("--mode", choices=("full", "context_only", "review_only"), default="full")
    parser.add_argument("--image", default="skillrelay:1.0")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.case, args.output = args.case.resolve(), args.output.resolve()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    from skillrelaybench.harness import load_case
    from skillrelaybench.check import check_runtime
    spec = load_case(args.case)
    if args.variant not in spec["variants"]:
        parser.error("Unknown case variant")
    source = args.case.parent / spec["variants"][args.variant]["source"]
    if args.output.is_relative_to(source) or args.case.is_relative_to(args.output):
        parser.error("Output must be separate from case inputs")
    check_runtime(args.image, args.agent, guarded=True)
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.case, args.output / "case-frozen.json")
    import skillrelaybench
    import skillrelayguard
    import skillrelayruntime
    for package in (skillrelaybench, skillrelayguard, skillrelayruntime):
        shutil.copytree(Path(package.__file__).parent, args.output / "runtime-source" / package.__name__,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    args.preflight = True
    return worker(args)


if __name__ == "__main__":
    sys.exit(main())
