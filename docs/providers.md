# Model providers

Set credentials in the host environment, not in case files or source code.
The runtime places agent-provider credentials in a temporary gateway-only volume;
the tested agent receives placeholder credentials. Normal cleanup removes the
temporary volume.

## OpenAI / Codex

The default API root is `https://api.openai.com`. Set `OPENAI_API_KEY`, then use
`--agent codex --model MODEL_AVAILABLE_TO_YOUR_ACCOUNT`.

Evaluators use Codex independently of the tested agent. Guard attribution and
review use the Responses API with streaming and strict JSON-schema output.
Consequently, a Claude or Gemini experiment still needs a compatible Responses
provider for judging and, when enabled, defense.

## Claude

Set `ANTHROPIC_API_KEY` and use `--agent claude --model YOUR_CLAUDE_MODEL`.
The default root is `https://api.anthropic.com`.

If no API key is set, the runtime attempts to use a fresh host Claude login from
macOS Keychain or `~/.claude/.credentials.json`. That option requires a separately
installed and authenticated host Claude CLI. API-key authentication does not.
Refresh an expired login on the host before starting an experiment.

Keep `OPENAI_API_KEY` available for the independent evaluator and guard.

## Gemini

Set `SKILLRELAY_CHAT_URL` to a trusted **Chat Completions-compatible** API root
serving your Gemini model, set `SKILLRELAY_API_KEY` to that provider's key, and use
`--agent gemini --model YOUR_GEMINI_MODEL`.

The included adapter translates Gemini CLI requests to `/v1/chat/completions`.
It is **not** a native Google Gemini API transport. An OpenAI key alone does not
provide access to Google models.

Supported generation settings are `temperature`, `topP`, `maxOutputTokens`,
`stopSequences` and `responseMimeType` (`text/plain` or `application/json`).
Unsupported settings, including `thinkingConfig`, `topK`, `candidateCount`,
response schemas and `safetySettings`, return explicit errors before upstream
requests. Tool calling supports `AUTO`, `NONE` and `ANY`, not named-tool restrictions.
Compatibility depends on what the selected CLI and upstream provider request/support.

For a guarded Gemini run with OpenAI defense, also set:

```bash
export SKILLRELAYGUARD_API_KEY="$OPENAI_API_KEY"
export SKILLRELAYGUARD_UPSTREAM="https://api.openai.com"
```

For a subsequent **standalone evaluation** using OpenAI, select its key explicitly:

```bash
SKILLRELAY_API_KEY="$OPENAI_API_KEY" \
SKILLRELAY_RESPONSES_URL="https://api.openai.com" \
skillrelaybench evaluate \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --variant benign --run output/gemini-benign \
  --model gpt-5.4 --judge task --output output/gemini-benign-evaluation
```

The batch runner inherits one environment for execution and evaluation. When
those need different gateway keys, use `--skip-evaluation` and evaluate afterward
with the appropriate environment. The same applies to guarded batch evaluations.

## Settings reference

| Variable | Purpose / default |
| --- | --- |
| `OPENAI_API_KEY` | Default Responses/Chat provider key |
| `SKILLRELAY_API_KEY` | Responses/Chat key override; takes precedence over `OPENAI_API_KEY` |
| `SKILLRELAY_RESPONSES_URL` | Responses API root; default `https://api.openai.com` |
| `SKILLRELAY_CHAT_URL` | Required Gemini Chat Completions API root |
| `ANTHROPIC_API_KEY` | Claude API key |
| `SKILLRELAY_ANTHROPIC_URL` | Claude API root; default `https://api.anthropic.com` |
| `SKILLRELAYGUARD_API_KEY` | Guard key; falls back to `SKILLRELAY_API_KEY`, then `OPENAI_API_KEY` |
| `SKILLRELAYGUARD_UPSTREAM` | Guard Responses root; default `https://api.openai.com` |

API roots must not contain `/v1` at the end, embedded credentials, query strings
or fragments. For example, use `https://api.openai.com`, not its full request URL.

For a trusted local relay, use `host.docker.internal` in gateway endpoint settings
and a host-reachable address such as `127.0.0.1` for the host-side guard.
Inside containers, `127.0.0.1` refers to the container, not the host.
Only gateway/receiver services have host connectivity; the tested agent uses an
internal Docker network. Do not expose an unauthenticated relay publicly.

Provider overrides already set in your shell take precedence over defaults.
When returning to OpenAI, unset stale `SKILLRELAY_API_KEY`,
`SKILLRELAY_RESPONSES_URL`, `SKILLRELAYGUARD_API_KEY` and `SKILLRELAYGUARD_UPSTREAM`
overrides as appropriate; never print credential values to debug configuration.
