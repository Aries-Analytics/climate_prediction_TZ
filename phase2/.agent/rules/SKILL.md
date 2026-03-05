# HewaSense Global Rules — GOTCHA Framework

> Constitutional reference. Read this file on **every** model activation or switch.

---

## Project Laws (Non-Negotiable)

1. **NO SYNTHETIC FALLBACKS** — Never return dummy/mock/fabricated data if an API or data source fails. Raise `DataSourceConnectionError` with a clear message instead.
2. **NO PREDICT_PROBA** — Regression models must use `.predict()`. Never `.predict_proba()`.
3. **AUDITOR GATE** — Only in Auditor mode can you run `git merge`. No exceptions.
4. **HANDOVER** — Upon any model activation, read `state.json`, this file, and `args/persona_config.yaml` before doing anything.
5. **DATA TRUTH** — UTC-aware datetimes everywhere. `datetime.now(timezone.utc)`, never naive `datetime.now()`.
6. **FEATURE ALIGNMENT** — ML serving must match training: **77 features** defined in `feature_schema.json`. Never retrain on fewer features.
7. **CONTRACT COMPLIANCE** — Frontend consumes Backend API contracts exactly as defined in `state.json → shared_contract`. No frontend-side overrides.
8. **AUTONOMOUS DOCUMENTATION** — After any model retraining, feature schema change, config update, or pipeline modification, the agent MUST automatically update all affected documentation files before marking the task complete. This includes:
   - `docs/current/EXECUTIVE_SUMMARY.md` (metrics, feature counts)
   - `docs/references/ML_MODEL_REFERENCE.md` (model details)
   - `docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md` (project overview)
   - `feature_schema.json` (feature names and count)
   - `args/persona_config.yaml` (expected_feature_count)
   - `state.json → shared_contract` (expected_feature_count)
   - `docs/HewaSense Agentic DevOps/HewaSense_Technical_Reference_v5_FINAL.txt`
   - All `docs/references/` files referencing model metrics or feature counts
   - `goals/stabilization_sprint.md` and any goal files referencing feature counts
   - `memory/MEMORY.md` (persistent memory facts)
   - `context/ml_serving_rules.md` (ML serving rules)
   - `README.md` (project README)
   - **Never consider a code change "done" until docs are synchronized.**
9. **SPRINT LIFECYCLE** — When the last issue in a sprint is resolved:
   a. Mark the issue `"resolved"` in `state.json` with `resolved_date` and `fix` description
   b. Set `resolved` count = `total_issues` in `state.json → task_board`
   c. Run `audit.py` → must exit 0
   d. Mark the verification checklist in the goal file (e.g., `goals/stabilization_sprint.md`)
   e. Update `state.json → project_metadata.phase` to the next phase
   f. Update `persona_config.yaml`: `current_phase`, `sprint_phase: 0`, `active_persona: orchestrator`
   g. Update `memory/MEMORY.md` with sprint completion status
   h. **Never leave a sprint open when all issues are resolved.**

---

## GOTCHA Layer Map

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Goals** | `goals/` | Process definitions per workflow (stabilization, features, ingestion) |
| **Orchestration** | *You (the AI)* | Read goals, apply args, delegate to tools |
| **Tools** | `tools/` + `backend/scripts/` | Deterministic scripts. Listed in `tools/manifest.md` |
| **Context** | `context/` | Domain knowledge (climate, ML rules, API contracts) |
| **Hard Prompts** | `hardprompts/` | Reusable instruction templates (handover, rejection reports) |
| **Args** | `args/` | Behavior settings: active persona, phase, constraints |

---

## Persona Reading Order

**Before starting work as any persona, read in this order:**

### Orchestrator Mode
1. `state.json` → current tasks, progress, shared contracts
2. `args/persona_config.yaml` → active phase and constraints
3. `goals/manifest.md` → find the relevant goal workflow
4. The specific goal file → follow its ATLAS process

### Backend Architect Mode
1. `state.json` → which issues are assigned to you
2. `context/ml_serving_rules.md` → feature alignment, predict rules
3. `context/hewasense_domain.md` → climate science reference
4. `tools/manifest.md` → check existing scripts before writing new ones

### Frontend Engineer Mode
1. `state.json → shared_contract` → exact API schemas to consume
2. `context/api_contracts.md` → endpoint reference
3. `tools/manifest.md` → existing frontend utilities

### Auditor Mode
1. `state.json → auditor_feedback` → previous audit trail
2. Run `python audit.py` → automated violation scan
3. `hardprompts/rejection_report.md` → template if blocking merge
4. `goals/` → verify work matches goal acceptance criteria

---

## Memory Protocol

**Load at session start:**
1. Read `memory/MEMORY.md` for curated facts and preferences
2. Read today's log: `memory/logs/YYYY-MM-DD.md`
3. Read yesterday's log for continuity

**During session:**
- Log notable events: `python tools/memory/memory_write.py --content "event" --type event`
- Add facts: `python tools/memory/memory_write.py --content "fact" --type fact --importance 7`

**Search past context:**
- `python tools/memory/hybrid_search.py --query "what was decided about feature X"`

---

## Guardrails — Learned Behaviors

- Always check `tools/manifest.md` before writing a new script
- Verify tool output format before chaining into another tool
- Don't assume APIs support batch operations — check first
- When a workflow fails mid-execution, preserve intermediate outputs before retrying
- Read the full goal before starting a task — don't skim
- When a goal exceeds reasonable length, propose splitting into primary goal + technical reference
- **DOCUMENTATION CHECKPOINT**: After completing any task that modifies models, features, configs, or pipelines, run a grep sweep for stale numbers (old feature counts, old metrics) in `docs/` before closing the task. Use `grep_search` for old values and update all active docs (skip `docs/archive/`).
- **DOC SYNC TRIGGER**: If you retrain models or change `feature_schema.json`, immediately update all 8+ docs files listed in Law #8 — don't wait for the user to ask.
- **SPRINT AUTO-CLOSE**: After resolving any issue, check `state.json → task_board.resolved` vs `total_issues`. If they match, execute Law #9 immediately — don't wait for the user to notice.

*(Add new guardrails as mistakes happen. Keep under 15 items.)*

---

*Last updated: 2026-02-25*
