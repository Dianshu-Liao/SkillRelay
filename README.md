# SkillRelay

Run **SkillRelayBench**, a benchmark of cross-session skill-composition attacks,
and **SkillRelayGuard**, a runtime defense that restores artifact-origin context
and reviews operations.

Use the included cases and software to run your own baseline and guarded
experiments.

## Requirements

- Linux or macOS; on Windows, use WSL2 with Docker integration.
- Python 3.12+ and a running Docker daemon.
- Access to the selected model APIs. Agent execution, judging and defense calls
  incur charges. Set provider spending limits and start with one benign case.

Agent CLIs run inside Docker; you do not need to install them on the host.
The image pins Codex 0.140.0, Claude Code 2.1.207 and Gemini CLI 0.61.0.

## 1. Install

Open a terminal at the root of your downloaded repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
docker build -t skillrelay:1.0 implementation/docker
```

The Python package has no third-party runtime dependencies. Building requires
setuptools and access to Debian, npm and Python package registries.

The examples below use Codex and OpenAI. Choose models available to your account.
In **Bash**, enter the API key without adding it to your shell history:

```bash
read -r -s -p "OpenAI API key: " OPENAI_API_KEY
printf '\n'
export OPENAI_API_KEY
skillrelay-check --agent codex --guarded
```

On macOS, run `bash` first if your terminal uses zsh. The check verifies Docker,
the image and endpoint syntax; it does not authenticate or call a model.
For Claude, Gemini or a custom endpoint, see [provider configuration](docs/providers.md).

## 2. Run the benchmark

### Start with one benign case

Validate the case without Docker or API calls:

```bash
skillrelaybench validate \
  --case benchmark/cases/CS-01-IP-instructions/case.json
```

Run its two tasks in separate agent sessions:

```bash
skillrelaybench run \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --variant benign --agent codex --model gpt-5.3-codex \
  --output output/benign-baseline
```

The workspace persists between sessions, but the agent home and conversation
session are reset. Each output path must be **new**; existing runs are never
overwritten.

Evaluate task completion with an independent judge:

```bash
skillrelaybench evaluate \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --variant benign --run output/benign-baseline \
  --model gpt-5.4 --judge task \
  --output output/benign-baseline-evaluation
```

The verdict is in `output/benign-baseline-evaluation/evaluation.json`.
Successful execution alone is not a task-success judgment.

### Run an attack case

This command runs and evaluates the adversarial version of the same case:

```bash
skillrelaybench pipeline \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --variant ip-instructions --agent codex --model gpt-5.3-codex \
  --judge-model gpt-5.4 --output output/attack-baseline
```

Read `output/attack-baseline/run/run-summary.json` for execution status and
`output/attack-baseline/evaluation/evaluation.json` for task and attack judgments.

**Run attack inputs only through the isolated runtime.** Do not install the
benchmark's skills in your personal agent environment or execute their scripts
directly on the host.

### Select cases or run a batch

[benchmark/catalog.json](benchmark/catalog.json) lists all **270 cases** across
30 scenarios, ten domains, three attack patterns and three injection surfaces.
Each entry gives the case configuration and its adversarial variant name.
Use catalog IDs for batch selection; the runner resolves their configuration paths.

Preview a three-case batch without running anything:

```bash
python scripts/run_benchmark.py \
  --cases CS-01-IP-instructions CS-01-IP-code CS-01-IP-resources \
  --variant adversarial --agent codex --model gpt-5.3-codex \
  --mode baseline --output output/baseline-three --dry-run
```

Remove `--dry-run` to execute. The script runs cases **serially**, evaluates each
one, and writes `batch.json` plus `summary.json` under the output directory.
Use `--variant benign --judge task` for task-only benign evaluations, or
`--skip-evaluation` to run without judges.

To select all cases, replace `--cases ...` with `--all`:

```bash
python scripts/run_benchmark.py \
  --all --variant adversarial --agent codex --model gpt-5.3-codex \
  --mode baseline --output output/baseline-all --dry-run
```

Inspect the plan and costs before removing `--dry-run`: a full suite schedules
540 agent sessions plus evaluation calls. There are no automatic retries.
On a nonzero execution/evaluation exit, the batch stops, preserves logs and marks
remaining cases pending. It does not produce an aggregate for a partial batch.
Choose the remaining case IDs and a new output directory when continuing.

## 3. Use SkillRelayGuard

Run the same benign case with artifact-origin context and operation review:

```bash
skillrelayguard \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --variant benign --agent codex --model gpt-5.3-codex \
  --mode full --checker-model gpt-5.4 --attribution-model gpt-5.4 \
  --output output/benign-guard
```

Evaluate the guarded run:

```bash
skillrelayguard-evaluate \
  --run output/benign-guard \
  --case benchmark/cases/CS-01-IP-instructions/case.json \
  --judge-model gpt-5.4 --judge task \
  --output output/benign-guard-evaluation
```

The verdict is in
`output/benign-guard-evaluation/evaluation/evaluation.json`.
To run its attack variant, change `--variant benign` to `--variant ip-instructions`,
use new output directories, and use `--judge both` when evaluating.

For a guarded batch, use the same batch script with `--mode full`:

```bash
python scripts/run_benchmark.py \
  --cases CS-01-IP-instructions CS-01-IP-code CS-01-IP-resources \
  --variant adversarial --agent codex --model gpt-5.3-codex \
  --mode full --checker-model gpt-5.4 --attribution-model gpt-5.4 \
  --output output/guard-three --dry-run
```

| Mode | Artifact-origin context | Operation review |
| --- | --- | --- |
| `baseline` (batch script only) | Off | Off |
| `full` | On | On |
| `context_only` | On | Off |
| `review_only` | Off | On |

Attribution still runs in `review_only`, but its context is not injected.
Defense modes make additional model calls.

### Using your own tasks

The provided entry point runs **two-session tasks in the supplied isolated
runtime**, using Codex, Claude or Gemini. It is not a global plugin that
automatically protects arbitrary agents or existing host sessions.

To adapt it to your workflow, use a separate copy of
[the example case directory](benchmark/cases/CS-01-IP-instructions/).
Edit its two task prompts, expected skills and allowlisted inputs in `case.json`;
for a benign-only workflow, keep only the `benign` variant.
Validate the configuration, run `skillrelayguard --case ... --variant benign`,
and evaluate with `--judge task`. Supported service configurations are
`["receiver"]` and `["receiver", "workspace_sqlite"]`; other services need an
implementation adapter, not just a configuration name.
The frozen catalog and batch script are for the included benchmark; use the
single-case commands for your own tasks.

Operation review is **advisory**: the agent may revise, abandon or explicitly
confirm the exact reviewed request, including after a hold recommendation.
Review covers the provided submission adapter and receiver fallback.
Arbitrary local file changes, local SQLite publication and model-gateway traffic
are not operation-reviewed. Each guarded run writes its scope to `coverage.json`.

## 4. Read your results

Runs save their own traces and workspace snapshots under your chosen output path.
Guarded runs also save attribution, context and review records under `guard/`.
These generated files are ignored by Git when placed under `output/` or `results/`.

To summarize selected evaluations:

```bash
skillrelaybench summarize \
  output/benign-baseline-evaluation/evaluation.json \
  output/benign-guard-evaluation/evaluation/evaluation.json
```

| Metric key | Meaning |
| --- | --- |
| `benign_tsr` / `adversarial_tsr` | Task success rate (TSR) |
| `consequence_asr` | Attack success rate (ASR) |
| `strict_chain_asr` | Cross-session attack-chain success rate (ACSR) |

Groups distinguish tested agent, model, defense condition and judge configuration.
Baseline and guarded runs use the same task/attack judge prompts, verdict
validation and evidence-assembly rules. Guard diagnostics are retained separately,
not added as extra judge instructions or judge-only evidence.
`rate_all_scheduled` is a fraction from 0 to 1, with unknown and error states
retained in its denominator; `rate_among_adjudicated` uses only success/failure
verdicts. Task-only evaluations do not enter attack-rate denominators.
Execution and judging errors remain explicit; they are not successful defenses.

## Troubleshooting

- **Docker unavailable:** start Docker and run `skillrelay-check` again.
- **Image unavailable:** build the image using the installation command.
- **Authentication/model error:** verify account access and
  [provider settings](docs/providers.md); prerequisite checks do not test credentials.
- **Output already exists:** use a new output path.
- **Batch stopped:** inspect the failing case's `execution.log` or `evaluation.log`
  and the batch status. Fix the cause before paying for another run.
- **Moved a guarded run:** pass `--case` to its matching, unchanged configuration
  when evaluating. Case and input hashes are checked.

## Repository layout

| Path | Purpose |
| --- | --- |
| [benchmark/](benchmark/) | Catalog, case definitions, paired skills and task inputs |
| [implementation/skillrelaybench/](implementation/skillrelaybench/) | Execution and evaluation |
| [implementation/skillrelayguard/](implementation/skillrelayguard/) | Attribution, context and operation review |
| [implementation/skillrelayruntime/](implementation/skillrelayruntime/) | Docker isolation, gateways and receiver |
| [implementation/docker/](implementation/docker/) | Shared agent image |
| [scripts/run_benchmark.py](scripts/run_benchmark.py) | Batch selection, dry run, execution and summary |
| [docs/providers.md](docs/providers.md) | Model endpoint and credential configuration |

Run commands from this repository root with the virtual environment activated.
Use `--help` on each command for additional options.
