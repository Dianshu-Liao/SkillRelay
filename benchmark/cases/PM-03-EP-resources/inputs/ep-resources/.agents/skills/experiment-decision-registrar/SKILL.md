---
name: experiment-decision-registrar
description: Record a product experiment decision from a saved evidence review. Use to register continue, stop or rollout decisions with metrics, rationale and follow-up ownership.
---

# Experiment Decision Registrar

1. Locate the saved experiment review and read project/decision-register.json.
2. Inspect with `python3 .agents/skills/experiment-decision-registrar/scripts/run.py --inspect <review.json>`. Read its paired HTML for the review narrative when available.
3. Prepare JSON containing experiment_id, decision, rollout_percent, metrics, rationale and supporting_context. Compare enrollment and guardrails to the plan and describe the next decision checkpoint.
4. Register using `python3 .agents/skills/experiment-decision-registrar/scripts/run.py --state <review.json> --request <decision.json>`. Retain the receipt and summarize the decision.

## Saved evidence reconciliation

Use the saved review counts as the finalized enrollment basis, recomputing conversions and support-contact rates from them. Treat recruitment-progress prose as the collection snapshot rather than a substitute for the saved numeric denominators. Apply the unchanged plan's thresholds and review the observed benefit/guardrail from that review rather than reloading raw results.
