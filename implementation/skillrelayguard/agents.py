"""CLI-specific wiring; defense policy and context remain provider-independent."""

import json


MODELS = {"codex": "gpt-5.3-codex", "claude": "claude-sonnet-4-6", "gemini": "gemini-3.6-flash"}


def hook_settings(agent, enabled=True, pretool=False):
    event = "AfterTool" if agent == "gemini" else "PostToolUse"
    hook = {"type": "command", "command": "python3 /opt/guard/timing.py --module 2 --hook /opt/guard/hook.py",
            "timeout": 5000 if agent == "gemini" else 5}
    settings = {"hooks": {event: [{"matcher": ".*" if agent == "gemini" else "*", "hooks": [hook]}]}} if enabled else {"hooks": {}}
    if agent == "codex" and enabled:
        settings["hooks"][event][0].pop("matcher")
    if agent == "gemini":
        settings.update(security={"auth": {"selectedType": "gemini-api-key"}}, hooksConfig={"enabled": enabled})
    if agent == "claude" and enabled:
        settings["hooks"]["PostToolUseFailure"] = settings["hooks"]["PostToolUse"]
    if pretool and enabled:
        before = "BeforeTool" if agent == "gemini" else "PreToolUse"
        settings["hooks"][before] = [{"hooks": [{"type": "command",
            "command": "python3 /opt/guard/timing.py --module 3 --hook /opt/guard/pretool_hook.py", "timeout": 300000 if agent == "gemini" else 300}]}]
        settings["hooks"]["SessionStart"] = [{"hooks": [{"type": "command",
            "command": "python3 /opt/guard/timing.py --module 3 --hook /opt/guard/pretool_hook.py", "timeout": 5000 if agent == "gemini" else 5}]}]
    return settings


def hook_mount(agent):
    return {"codex": "/etc/codex/hooks.json", "claude": "/opt/guard/settings.json",
            "gemini": "/opt/guard/settings.json"}[agent]


def prepare_command(agent, command):
    command = list(command)
    if command[0] != agent:
        return command
    if agent == "codex":
        command[1:1] = ["--dangerously-bypass-hook-trust"]
    elif agent == "claude":
        command += ["--settings", "/opt/guard/settings.json"]
        command = ["sh", "-c", 'mkdir -p "$HOME/.claude"; ln -sfn /workspace/.agents/skills "$HOME/.claude/skills"; exec "$@"',
                   "claude-guard-bootstrap", *command]
    return command


def tool_evidence(event):
    item = event.get("item", {})
    if event.get("type") == "item.completed" and item.get("type") == "command_execution":
        return "\n".join(["TOOL ID: " + str(item.get("id")), "COMMAND:", item.get("command", ""),
                          "EXIT CODE: " + str(item.get("exit_code")), "OUTPUT:", item.get("aggregated_output", "")])
    if event.get("type") == "item.completed" and item.get("type") == "file_change":
        return "NATIVE FILE CHANGE EVENT (paths/status only, not patch bytes):\n" + json.dumps(item, ensure_ascii=False)
    if event.get("type") in ("tool_use", "tool_result"):
        return json.dumps(event, ensure_ascii=False, indent=2)
    if event.get("type") in ("assistant", "user"):
        content = event.get("message", {}).get("content", [])
        if isinstance(content, list):
            blocks = [block for block in content if isinstance(block, dict) and block.get("type") in ("tool_use", "tool_result")]
            if blocks:
                return json.dumps(blocks, ensure_ascii=False, indent=2)
    return None


def usage_from_output(agent, output):
    events = []
    for line in output.splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except ValueError:
            continue
    if agent == "codex":
        terminal = [event["usage"] for event in events if event.get("type") == "turn.completed"]
        if len(terminal) != 1:
            raise ValueError("Expected one completed Codex turn")
        usage = terminal[0]
        input_tokens, cache, output_tokens = usage["input_tokens"], usage["cached_input_tokens"], usage["output_tokens"]
    elif agent == "claude":
        terminal = [event["usage"] for event in events if event.get("type") == "result" and "usage" in event]
        if len(terminal) != 1:
            raise ValueError("Expected one Claude result usage record")
        usage = terminal[0]
        cache = usage.get("cache_read_input_tokens", 0)
        input_tokens = usage["input_tokens"] + cache + usage.get("cache_creation_input_tokens", 0)
        output_tokens = usage["output_tokens"]
    else:
        terminal = [event["stats"] for event in events if event.get("type") == "result" and event.get("status") == "success" and "stats" in event]
        if len(terminal) != 1:
            raise ValueError("Expected one Gemini result stats record")
        usage = terminal[0]
        input_tokens, cache = usage["input_tokens"], usage["cached"]
        output_tokens = usage["total_tokens"] - input_tokens
        if output_tokens < usage["output_tokens"]:
            raise ValueError("Gemini token accounting requires reconciliation")
    return {"input": input_tokens, "cache": cache, "output": output_tokens, "total": input_tokens + output_tokens}


def execution_sources(output):
    sources, calls = {}, {}
    for number, line in enumerate(output.splitlines(), 1):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "item.completed":
            evidence = tool_evidence(event)
            if evidence is not None:
                sources[f"tool:{number}"] = {"text": evidence}
            continue
        if event.get("type") in ("assistant", "user"):
            content = event.get("message", {}).get("content", [])
            blocks = content if isinstance(content, list) else []
        else:
            blocks = [event]
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                identifier = block.get("id") or block.get("tool_id")
                if identifier:
                    calls[identifier] = block
            elif block.get("type") == "tool_result":
                identifier = block.get("tool_use_id") or block.get("tool_id")
                if identifier in calls:
                    call = calls[identifier]
                    parameters = call.get("input", call.get("parameters", {}))
                    content = block.get("content", block.get("output", ""))
                    if isinstance(content, list):
                        content = "\n".join(part.get("text", json.dumps(part, ensure_ascii=False))
                                            if isinstance(part, dict) else str(part) for part in content)
                    elif not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False, indent=2)
                    arguments = "\n".join(str(key) + ": " + (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
                                          for key, value in parameters.items())
                    sources[f"tool:{number}:{index}"] = {"text": "\n".join([
                        "TOOL ID: " + identifier, "TOOL: " + str(call.get("name", call.get("tool_name"))),
                        "ARGUMENTS:", arguments, "RESULT STATUS: " + str(block.get("status", "error" if block.get("is_error") else "returned")),
                        "OUTPUT:", content])}
    return sources
