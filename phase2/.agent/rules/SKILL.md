# HewaSense Global Rules — GOTCHA Framework

> Constitutional reference. Read this file at the start of any substantial session.
>
> **Active context:** CLAUDE.md (repo root) is the file the agent harness auto-loads
> on every session. The persona framework below (Orchestrator / Backend Architect /
> Frontend Engineer / Auditor) is **documentation of an architectural intent** — it
> is not currently wired to runtime automation. Keep it in mind as a mental model
> for separating concerns, but do not expect `persona_config.yaml` or `state.json`
> to drive behaviour today.

---

## Project Laws (Non-Negotiable)

1. **NO SYNTHETIC FALLBACKS** — Never return dummy/mock/fabricated data if an API or data source fails. Raise `DataSourceConnectionError` with a clear message instead.
2. **NO PREDICT_PROBA** — Regression models must use `.predict()`. Never `.predict_proba()`.
3. **AUDITOR GATE** — Only in Auditor mode can you run `git merge`. No exceptions.
4. **DATA TRUTH** — UTC-aware datetimes in application code; **tz-naive `date` objects in ingestion modules** per the ingestion tz contract (`backend/utils/dates.py`, established 2026-04-16 after four tz patches proved the value of a single convention).
5. **FEATURE ALIGNMENT** — ML serving must match training: **83 features** defined in `outputs/models/feature_selection_results.json`. Never retrain on fewer features.
6. **CONTRACT COMPLIANCE** — Frontend consumes Backend API responses exactly as defined in the shared API contracts (see `context/api_contracts.md`). No frontend-side schema overrides.
7. **AUTONOMOUS DOCUMENTATION** — After any model retraining, feature schema change, config update, or pipeline modification, the agent MUST automatically update all affected documentation files before marking the task complete. This includes:
   - `docs/current/EXECUTIVE_SUMMARY.md` (metrics, feature counts)
   - `docs/references/ML_MODEL_REFERENCE.md` (model details)
   - `docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md` (project overview)
   - `outputs/models/feature_selection_results.json` (feature names and count — canonical)
   - `docs/HewaSense Agentic DevOps/HewaSense_Technical_Reference_v5_FINAL.txt`
   - All `docs/references/` files referencing model metrics or feature counts
   - `goals/stabilization_sprint.md` and any goal files referencing feature counts
   - `memory/MEMORY.md` (persistent memory facts)
   - `context/ml_serving_rules.md` (ML serving rules)
   - `README.md` (project README)
   - **Never consider a code change "done" until docs are synchronized.**
8. **SESSION LOGGING** — Every work session ends with an entry in `memory/logs/YYYY-MM-DD.md` and a row in `memory/MEMORY.md` Logs Index. Skipping is a protocol violation (hit this on 2026-04-14 — Apr 14 session log was written but MEMORY.md Logs Index + "Last updated" were not, caught by Walter on 2026-04-15).

---

## GOTCHA Layer Map

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Goals** | `goals/` | Process definitions per workflow (stabilization, features, ingestion) |
| **Orchestration** | *You (the AI)* | Read goals, apply rules, delegate to tools |
| **Tools** | `tools/` + `backend/scripts/` | Deterministic scripts. Listed in `tools/manifest.md` |
| **Context** | `context/` | Domain knowledge (climate, ML rules, API contracts) |
| **Hard Prompts** | `hardprompts/` | Reusable instruction templates (handover, rejection reports) |
| **Args** | `args/persona_config.yaml` | Forbidden-pattern config for `scripts/audit.py` (only live use) |

---

## Persona Mental Model (aspirational — not runtime-wired)

Even though personas are not mechanically enforced, the separation of concerns is
a useful mental check before starting a task:

- **Orchestrator** — reads goals, coordinates, does not write code
- **Backend Architect** — ML serving, pipelines, DB, ingestion (needs `context/ml_serving_rules.md`, `context/hewasense_domain.md`)
- **Frontend Engineer** — React dashboards, API consumption (needs `context/api_contracts.md`)
- **Auditor** — merge gate, runs `scripts/audit.py` before any merge

---

## Memory Protocol

**Load at session start:**
1. CLAUDE.md (repo root) — auto-loaded by the harness
2. `memory/MEMORY.md` — curated facts, preferences, project state
3. `memory/logs/YYYY-MM-DD.md` for today + yesterday — continuity

**During session:**
- Log notable events in `memory/logs/YYYY-MM-DD.md`
- Add durable facts to `memory/MEMORY.md` Key Facts section
- Do **not** add ephemeral session details to Key Facts — only durable facts belong there

**End of session:**
- Append row to `memory/MEMORY.md` Logs Index (one-line summary)
- Update `Last Updated` date at bottom of MEMORY.md
- Commit and push

---

## Guardrails — Learned Behaviors

- Always check `tools/manifest.md` before writing a new script
- Verify tool output format before chaining into another tool
- Don't assume APIs support batch operations — check first
- When a workflow fails mid-execution, preserve intermediate outputs before retrying
- Read the full goal before starting a task — don't skim
- When a goal exceeds reasonable length, propose splitting into primary goal + technical reference
- **DOCUMENTATION CHECKPOINT**: After completing any task that modifies models, features, configs, or pipelines, run a grep sweep for stale numbers in `docs/` before closing the task. Update all active docs (skip `docs/archive/`).
- **DOC SYNC TRIGGER**: If you retrain models or change `feature_schema.json`, immediately update all 8+ docs files listed in Law #7 — don't wait for the user to ask.
- **Ingestion TZ Contract (2026-04-16)** — All 5 ingestion modules use tz-naive `date` objects per `backend/utils/dates.py`. Zero `datetime.now(timezone.utc)` below the public API boundary. Never mix tz-aware and tz-naive values in the ingestion layer — four production bugs (Apr 6/7/9/16 of 2026) were caused by exactly that mixing and were only eliminated by the unified contract.
- **Single Source of Truth (2026-04-15)** — Duplicate directory pairs are drift traps. `phase2/modules/` + `phase2/utils/` were deleted after the stale copy shadowed the corrected `backend/modules/` and produced 12 forecasts/day instead of 24 for 2 days. If you find two directories with the same apparent purpose, consolidate them and delete one.
- **Shadow Run Gap Policy (2026-04-16)** — Daily forecast gaps are acceptable ONLY when caused by server/infrastructure downtime. Code/config bugs are NOT acceptable gap causes — fix the bug and backfill the day via the manual runbook (`memory/logs/2026-04-16.md`).

*(Add new guardrails as mistakes happen. Keep under 15 items.)*

---

*Last updated: 2026-04-16*
