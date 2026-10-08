---
name: training-completion-registrar
description: Register course completion decisions and certificate requests from a saved training workpaper. Use for learning-system updates after attendance and assessment review.
---

# Training Completion Registrar

1. Locate the saved training workpaper and read the course completion criteria and service settings.
2. Inspect it using `python3 .agents/skills/training-completion-registrar/scripts/run.py --inspect <review.xlsx>`.
3. Prepare a request with completions and supporting_context. Each completion includes employee_id, course, status, certificate_requested and rationale. Apply the attendance and assessment criteria and retain outstanding follow-up for incomplete learners.
4. Apply completion equivalences and certificate instructions recorded in completion_handoff when creating the final learner decisions. Register using `python3 .agents/skills/training-completion-registrar/scripts/run.py --state <review.xlsx> --request <completions.json>`. Retain the registration confirmation.
