# Model Handover Prompt Template

> Use this exact prompt when switching models in Antigravity IDE.
> Adapt only the final sentence to match the active task.

---

## Template

```
I have switched models for context. Please initialize by reading these files in order:

1. .agent/rules/SKILL.md — project laws and GOTCHA layer map
2. state.json — current task board, shared contracts, auditor feedback
3. args/persona_config.yaml — active persona, sprint phase, forbidden patterns
4. goals/manifest.md — find the relevant active goal workflow

Identify the current branch and the last Auditor report in state.json.
Resume the task of [DESCRIBE ACTIVE TASK] without using placeholders or synthetic data.
```

---

## Example (during stabilization Phase 2)

```
I have switched models for context. Please initialize by reading these files in order:

1. .agent/rules/SKILL.md
2. state.json
3. args/persona_config.yaml
4. goals/manifest.md

Identify the current branch and the last Auditor report in state.json.
Resume the task of fixing Issue 4 (predict_proba → .predict) in forecast_service.py without using placeholders or synthetic data.
```

---

## Example (during feature expansion)

```
I have switched models for context. Please initialize by reading these files in order:

1. .agent/rules/SKILL.md
2. state.json
3. args/persona_config.yaml
4. goals/manifest.md

Identify the current branch and the last Auditor report in state.json.
Resume building the new Early Warning notification feature without using placeholders or synthetic data.
```
