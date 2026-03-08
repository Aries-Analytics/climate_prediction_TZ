# GOTCHA Framework: Agent Prompt Triggers

> This document contains reusable prompt templates to force AI agents to comply with the GOTCHA framework and its memory protocol. You can copy and paste these during your sessions.

---

## 1. The "Start of Session" Context Loader

*Use this right after you open a new chat instance to ensure the fresh agent reads the foundational rules and what the previous agent was doing.*

```markdown
Before we begin the next task, execute your handover protocol:
1. Read `memory/MEMORY.md` (in-repo GOTCHA memory) AND the Claude Code project memory at `C:\Users\YYY\.claude\projects\...\memory\MEMORY.md` — load the current system state, known bugs, and architecture rules. If they differ, the Claude Code memory is more recent.
2. Read today's and yesterday's daily logs in `memory/logs/` — catch up on recent fixes and decisions.
3. Run `git log --oneline -10` — check the last 10 commits to see what code changed.
4. Read `goals/manifest.md` and `goals/shadow_run_implementation.md` — confirm current phase and active goals.
5. SSH to the server and check `docker ps` and the last 20 lines of scheduler logs to confirm current operational status.

After loading, give me a one-paragraph briefing: what the system's current state is, what was done last session, and what the most important open risk or pending action is. Then confirm you are ready.
```

---

## 2. The "Mid-Session Insight" Trigger

*Use this when we've just spent time debugging a weird issue, or when you make a specific technical decision you want the agent to remember (like a specific library version or configuration choice).*

```markdown
That worked. Right now, before we move on:
1. Append to today's in-repo log:
   `python tools/memory/memory_write.py --content "<symptom> → <root cause> → <fix: file:line>" --type insight --importance 8`
2. If this is a structural fact that must survive across sessions (a bug fix pattern, an architecture rule, a gotcha), also update `memory/MEMORY.md` directly using the Edit tool — specifically the "Known Bugs Fixed" or "Learned Behaviors" section.
3. If it changes Claude Code's understanding of how the system works, update the Claude Code project memory at `C:\Users\YYY\.claude\projects\...\memory\MEMORY.md` too.

Note: Two memory tiers exist — `phase2/memory/` (in-repo GOTCHA memory, tooled) and the `.claude` project memory (Claude Code native, auto-loaded each session). Critical facts go in both.
```

---

## 3. The "End of Session / Sprint Wrap-up" Trigger

*Use this when we've finished a major feature or solved a big ticket, right before you close out for the day.*

```markdown
We are done with this feature/sprint. Before we close out, execute the GOTCHA Sprint End protocol:
1. Write a clean, formatted daily log for today at `memory/logs/YYYY-MM-DD.md`. Include: Issues Diagnosed & Fixed (symptom → root cause → fix → commit), Dashboard State table, Shadow Run Status, and a Learned Behaviors section at the bottom.
2. Update `memory/MEMORY.md`: append new Known Bugs Fixed entries, update any stale facts, update the Logs Index.
3. Run a doc sweep (see Trigger #5) specifically looking for:
   - Any status that should have changed (pending → active, planned → live, upcoming → complete)
   - Any stale dates in "Last Updated", "Date:", or "Updated:" fields in docs we touched
   - Any doc that contradicts code we just wrote
4. Stage, commit, and push all changed files (docs + code). Then `git pull` on the server.
```

---

## 4. The "Data Leakage / Architecture Shift" Trigger

*Use this if we ever change the core ML features, thresholds, model metrics, or API responses — things that break backward compatibility.*

```markdown
Since we just modified [feature count / payout threshold / model architecture / metric values], you are mandated by GOTCHA Law #8 (Autonomous Documentation) to sync the system before doing anything else.

Find and update ALL occurrences of the old value in:
- `docs/current/` — all files
- `docs/references/` — all files
- `docs/Kilombero Pilot/` — all files
- `goals/` — manifest and shadow run implementation
- `context/` — hewasense_domain.md and ml_serving_rules.md
- `memory/MEMORY.md` — Known Bugs Fixed, Forecast Structure, Data Assets sections

Search pattern: grep for the old number/value across all those directories. Replace every instance. Then re-grep to verify zero remaining occurrences. Do NOT touch `docs/archive/` or `docs/reports/` (historical).
```

---

## 5. The "Global Doc Sweep & Sync" Trigger

*Use this when you want to force a comprehensive hunt across the entire project for ALL classes of stale information — not just metric values.*

```markdown
Execute a global documentation sweep across `docs/current/`, `docs/references/`, `docs/Kilombero Pilot/`, `goals/`, `context/`, and `memory/`. Do NOT touch `docs/archive/` or `docs/reports/`.

Search for ALL four staleness classes — not just the obvious one:

CLASS 1 — Stale metrics/numbers: grep for the old value and replace with the new one.

CLASS 2 — Stale status transitions: grep for words like "pending", "planned", "upcoming", "scheduled", "will be", "future" in the context of things that are now ACTIVE or COMPLETE. Check every "Current Status", "Document Status", "Next Steps", and "Status:" field explicitly.

CLASS 3 — Stale dates: grep for "Last Updated", "Date:", "Updated:" fields and check if they reflect the last actual change to that document.

CLASS 4 — Command/syntax staleness: grep for `docker-compose` (v1), old cron expressions (`0 3 * * *`), `PIPELINE_TIMEZONE=UTC`, or any other deprecated config values.

After replacing, re-grep each class to verify zero remaining stale instances. Write a walkthrough summary listing every file changed, what was wrong, and what was fixed. Then commit and push.
```

---

## 6. The "Operational Status Change" Trigger

*Use this whenever the system transitions to a new operational state: shadow run goes live, first pipeline run fires, evidence pack threshold reached, underwriter engagement begins, etc.*

```markdown
We just reached a new operational milestone: [describe the milestone — e.g., "shadow run day 1 pipeline ran successfully", "first Brier Score evaluated", "Evidence Pack sent to underwriter"].

Execute the operational status update:
1. Update every "Current Status", "Document Status", "Status:", and "Next Steps" section in:
   - `docs/current/EXECUTIVE_SUMMARY.md`
   - `docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md`
   - `docs/Kilombero Pilot/KILOMBERO_BASIN_PILOT_SPECIFICATION.md`
   - `goals/shadow_run_implementation.md`
   - `goals/manifest.md`
2. Write a daily log entry in `memory/logs/YYYY-MM-DD.md` marking this milestone with exact timestamp and evidence (log output, Slack message, DB count, etc.).
3. Update `memory/MEMORY.md` to reflect the new operational reality (e.g., "Shadow run Day N complete", "Brier Scores available", etc.).
4. Commit and push all changes with a commit message that names the milestone explicitly.
```

---

## 7. The "Server Health Check" Trigger

*Use this at the start of any session where you will interact with the server, or after any incident (container crash, DB wipe, missed pipeline run).*

```markdown
Before we touch anything on the server, run a full health check:
1. `docker ps` — confirm all 5 containers are Up: climate_db_dev, climate_backend_dev, climate_frontend_dev, climate_pipeline_scheduler_dev, climate_pipeline_monitor_dev.
2. Last 30 lines of scheduler logs — confirm "Next scheduled run: YYYY-MM-DD 06:00:00+03:00" (EAT, not UTC).
3. DB record counts — run inside climate_backend_dev:
   - `SELECT COUNT(*) FROM climate_data;` → expect 1878+
   - `SELECT COUNT(*) FROM model_metrics;` → expect 4
   - `SELECT COUNT(*) FROM forecast_logs;` → expect N × 12 (where N = shadow run days elapsed)
4. `git log --oneline -3` on the server — confirm it matches origin/phase2/feature-expansion HEAD.

Report the health check results before proceeding with any work.
```
