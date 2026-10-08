"""Translate native Gemini CLI requests to the configured Chat Completions endpoint."""

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time

from skillrelayruntime.evidence import append_record
from skillrelayruntime.gateway import Limits, reserve_global, credential_headers


def supported_fields(value, allowed, location):
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be an object")
    unsupported = set(value) - set(allowed)
    if unsupported:
        raise ValueError(f"Unsupported {location} fields: {', '.join(sorted(unsupported))}; refusing lossy translation")


def chat_request(body, model):
    supported_fields(body, ("systemInstruction", "contents", "tools", "toolConfig", "generationConfig"), "Gemini request")
    generation = body.get("generationConfig", {})
    supported_fields(generation, ("temperature", "topP", "maxOutputTokens", "stopSequences", "responseMimeType"),
                     "generationConfig")
    if "responseMimeType" in generation and generation["responseMimeType"] not in ("text/plain", "application/json"):
        raise ValueError("Unsupported generationConfig.responseMimeType; only text/plain and application/json are supported")
    tool_settings = body.get("toolConfig", {})
    supported_fields(tool_settings, ("functionCallingConfig",), "toolConfig")
    tool_config = tool_settings.get("functionCallingConfig", {})
    supported_fields(tool_config, ("mode",), "toolConfig.functionCallingConfig")
    mode = tool_config.get("mode", "AUTO")
    if mode not in ("AUTO", "NONE", "ANY"):
        raise ValueError("Unsupported toolConfig.functionCallingConfig.mode; refusing lossy translation")
    messages = []
    system = body.get("systemInstruction", {})
    if system:
        messages.append({"role": "system", "content": "\n".join(part["text"] for part in system.get("parts", []) if "text" in part)})
    pending = []
    for content in body.get("contents", []):
        role = "assistant" if content.get("role") == "model" else "user"
        texts, calls, responses = [], [], []
        for part in content.get("parts", []):
            if "text" in part:
                if not part.get("thought"):
                    texts.append(part["text"])
            elif "functionCall" in part:
                call = part["functionCall"]
                identifier = call.get("id") or f"call_{len(messages)}_{len(calls)}"
                calls.append({"id": identifier, "type": "function", "function": {
                    "name": call["name"], "arguments": json.dumps(call.get("args", {}))}})
                pending.append((call["name"], identifier))
            elif "functionResponse" in part:
                response = part["functionResponse"]
                match = next((entry for entry in pending if entry[0] == response["name"]), None)
                if match is None:
                    raise ValueError("Tool response without a corresponding call")
                pending.remove(match)
                responses.append({"role": "tool", "tool_call_id": match[1],
                                  "content": json.dumps(response.get("response", {}), ensure_ascii=False)})
            elif any(key in part for key in ("inlineData", "fileData", "executableCode", "codeExecutionResult")):
                raise ValueError("Unsupported non-text Gemini content; refusing lossy translation")
        if texts or calls:
            message = {"role": role, "content": "\n".join(texts) if texts else None}
            if calls:
                message["tool_calls"] = calls
            messages.append(message)
        messages.extend(responses)
    request = {"model": model, "messages": messages, "stream": False}
    tools = []
    for group in body.get("tools", []):
        if set(group) - {"functionDeclarations"}:
            raise ValueError("Unsupported Gemini server-side tool")
        for tool in group.get("functionDeclarations", []):
            supported_fields(tool, ("name", "description", "parametersJsonSchema", "parameters"), "functionDeclaration")
            if "parameters" in tool and "parametersJsonSchema" in tool:
                raise ValueError("Specify only one of functionDeclaration.parameters and parametersJsonSchema")
            tools.append({"type": "function", "function": {
                "name": tool["name"], "description": tool.get("description", ""),
                "parameters": normalize_schema(tool.get("parametersJsonSchema", tool.get("parameters", {"type": "object", "properties": {}})))}})
    if tools:
        request["tools"] = tools
    if tools:
        request["tool_choice"] = {"AUTO": "auto", "NONE": "none", "ANY": "required"}[mode]
    elif mode != "AUTO":
        raise ValueError("Explicit tool calling mode requires tools; refusing to discard it")
    for source, destination in (("temperature", "temperature"), ("topP", "top_p"), ("maxOutputTokens", "max_tokens"), ("stopSequences", "stop")):
        if source in generation:
            request[destination] = generation[source]
    if generation.get("responseMimeType") == "application/json":
        request["response_format"] = {"type": "json_object"}
    return request


def normalize_schema(value):
    if isinstance(value, list):
        return [normalize_schema(entry) for entry in value]
    if not isinstance(value, dict):
        return value
    result = {key: normalize_schema(entry) for key, entry in value.items()}
    if isinstance(result.get("type"), str):
        result["type"] = result["type"].lower()
    return result


def gemini_response(response):
    choices = response.get("choices", [])
    if not choices:
        raise ValueError("Upstream response contains no choices")
    choice = choices[0]
    message = choice.get("message")
    if message is None:
        if choice.get("finish_reason") == "content_filter":
            message = {}
        else:
            raise ValueError("Upstream returned no complete assistant message; inspect retained raw response")
    parts = []
    if message.get("content"):
        parts.append({"text": message["content"]})
    if message.get("refusal"):
        parts.append({"text": message["refusal"]})
    for call in message.get("tool_calls", []):
        function = call["function"]
        parts.append({"functionCall": {"id": call["id"], "name": function["name"], "args": json.loads(function["arguments"])}})
    finish = {"stop": "STOP", "tool_calls": "STOP", "length": "MAX_TOKENS", "content_filter": "SAFETY"}.get(choice.get("finish_reason"), "OTHER")
    usage = response.get("usage", {})
    return {"candidates": [{"index": 0, "content": {"role": "model", "parts": parts}, "finishReason": finish}],
            "modelVersion": response.get("model"),
            "usageMetadata": {"promptTokenCount": usage.get("prompt_tokens", 0),
                              "candidatesTokenCount": usage.get("completion_tokens", 0),
                              "cachedContentTokenCount": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
                              "thoughtsTokenCount": usage.get("reasoning_tokens", usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)),
                              "totalTokenCount": usage.get("total_tokens", 0)}}


def handler_for(model, upstream, limits):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_arguments):
            pass

        def respond(self, status, body, stream=False):
            raw = json.dumps(body, ensure_ascii=False).encode()
            payload = b"data: " + raw + b"\n\n" if stream else raw
            self.send_response(status)
            self.send_header("Content-Type", "text/event-stream" if stream else "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            self.respond(200 if self.path == "/health" else 404, {"ready": self.path == "/health"})

        def do_POST(self):
            try:
                route = re.fullmatch(r"/v1(?:beta)?/models/([^/:]+):(generateContent|streamGenerateContent)(?:\?alt=sse)?", self.path)
                if not route or route[1] != model:
                    raise ValueError("Only the configured Gemini model and generation endpoints are allowed")
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144 or self.headers.get("Content-Encoding", "identity") != "identity":
                    raise ValueError("Invalid request size or encoding")
                body = json.loads(self.rfile.read(size))
                request = chat_request(body, model)
                if not limits.reserve("gemini", model) or not reserve_global(Path("/budget/gemini-requests.jsonl")):
                    raise ValueError("Benchmark request budget exhausted")
                append_record(limits.path, {"event": "translation", "model": model, "route": self.path,
                                           "tools": [tool["function"]["name"] for tool in request.get("tools", [])],
                                           "messages": len(request["messages"]), "timestamp": time()})
                message = urllib.request.Request(upstream.rstrip("/") + "/v1/chat/completions", data=json.dumps(request).encode(),
                    headers={"Content-Type": "application/json", **credential_headers("gemini")}, method="POST")
                with urllib.request.urlopen(message, timeout=180) as response:
                    result = json.load(response)
                append_record(limits.path, {"event": "upstream_response", "body": result, "timestamp": time()})
                translated = gemini_response(result)
                append_record(limits.path, {"event": "response", "requested_model": model,
                                           "served_model": result.get("model"), "usage": result.get("usage"),
                                           "finish_reason": result["choices"][0].get("finish_reason"), "timestamp": time()})
                self.respond(200, translated, stream=route[2] == "streamGenerateContent")
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")[:4000]
                append_record(limits.path, {"event": "upstream_error", "status": error.code, "message": detail, "timestamp": time()})
                self.respond(error.code, {"error": {"code": error.code, "message": detail}})
            except Exception as error:
                append_record(limits.path, {"event": "gateway_error", "message": str(error), "timestamp": time()})
                self.respond(400, {"error": {"code": 400, "message": str(error)}})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["gemini"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--max-requests", type=int, default=80)
    arguments = parser.parse_args()
    upstream = os.environ.get("SKILLRELAY_CHAT_URL")
    if not upstream:
        parser.error("SKILLRELAY_CHAT_URL is required for the selected Gemini model")
    ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(arguments.model, upstream,
                                                     Limits(arguments.ledger, arguments.max_requests))).serve_forever()


if __name__ == "__main__":
    main()
