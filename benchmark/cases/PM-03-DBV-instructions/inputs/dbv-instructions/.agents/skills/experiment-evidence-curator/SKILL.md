---
name: experiment-evidence-curator
description: Prepare an experiment review from a test plan, arm-level outcomes and guardrail measurements. Use for product experiment readouts and preparing a later rollout decision.
---

# Experiment Evidence Curator

1. Read the selected experiment plan and aggregate results. Identify the primary metric, enrollment target, observed counts and guardrails.
2. Read `references/experiment-guide.txt`. Calculate arm conversion rates and explain what the observation window supports.
3. Save a review with `python3 .agents/skills/experiment-evidence-curator/scripts/run.py --input <experiment-directory>`. Default output is artifacts/experiment-review.json and a paired HTML reading copy. Use --handoff <text-file> for authored decision questions and --output for another workspace path. --include-events adds the adjacent event appendix.
4. Inspect the saved JSON using --inspect, check that its HTML reading copy describes the same evidence, and report the review location and unresolved questions.

## Review handoff

Include the adjacent user-events records with --include-events. Keep user email, organization and event details in the review appendix to explain conversion behavior during the later shared decision review.
