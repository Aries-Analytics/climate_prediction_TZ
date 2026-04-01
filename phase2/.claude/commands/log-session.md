# /log-session — Log Work Session (GOTCHA Protocol)

Run this at the end of any work session that involved code, business, infrastructure, documentation, or research. Handles everything that /log-run does NOT cover.

---

## Step 1 — Reconstruct what happened

Run the following to understand the session scope:

```bash
# Commits since last session log entry in MEMORY.md (compare against last date in Logs Index)
git log --oneline --since="YYYY-MM-DD" --no-walk=unsorted HEAD

# All files changed in those commits
git diff --name-only <first-commit-sha>^..HEAD

# Any uncommitted changes
git status
git diff --stat
```

Also read `memory/MEMORY.md` (Logs Index section) to find the last logged date — only log work since that date.

---

## Step 2 — Ask the user for session summary

If the git log does not fully capture what was done (e.g. research, business decisions, external calls, deferred items), ask:

> "What else happened this session that isn't visible in git? (e.g. decisions made, research done, opportunities evaluated, deferred items)"

Do NOT invent session content. Only log what is confirmed.

---

## Step 3 — Identify affected documentation

Based on the work done, determine which docs need updating. Use this guide:

| Work type | Docs to check/update |
|---|---|
| Business development / partnerships | `HEWASENSE_EXTERNAL_BRIEF.md`, `BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md` |
| Pricing / insurance product changes | `PARAMETRIC_INSURANCE_FINAL.md`, `BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md`, `HEWASENSE_EXTERNAL_BRIEF.md`, `PROJECT_OVERVIEW_CONSOLIDATED.md`, `CRITICAL_NUMBERS_VERIFICATION.md` |
| Frontend changes | `FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md`, `EXECUTIVE_SUMMARY.md` |
| Backend / pipeline changes | `DATA_PIPELINE_REFERENCE.md`, `AUTOMATED_PIPELINE_DEPLOYMENT.md`, `EXECUTIVE_SUMMARY.md` |
| ML model changes | **Stop — use /log-model-change instead** (Law #8 sweep required) |
| Infrastructure / deployment | `AUTOMATED_PIPELINE_DEPLOYMENT.md`, `SHADOW_RUN_DEPLOYMENT_GUIDE.md` |
| Roadmap / strategic decisions | `EXECUTIVE_SUMMARY.md`, `BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md` |
| Pilot / location changes | `KILOMBERO_BASIN_PILOT_SPECIFICATION.md`, `HEWASENSE_EXTERNAL_BRIEF.md` |

Only update docs where the content actually changed — do NOT touch docs just because they are listed above. Read the relevant section before deciding if an edit is warranted.

---

## Step 4 — Update Last Updated dates

For any doc that was meaningfully updated during this session, find its `**Last Updated**:` line and update the date to today.

---

## Step 5 — Append to or create daily log file

Check if `memory/logs/YYYY-MM-DD.md` already exists for today (a pipeline run may have created it).

**If it exists:** append a `## Session Notes` section at the bottom:
```markdown
---

## Session Notes — [Month Day]

[Bullet-point summary of what was done: decisions, changes, deferred items, opportunities evaluated]

**Docs updated this session:** [list]
```

**If it does not exist:** create `memory/logs/YYYY-MM-DD.md` with:
```markdown
# Daily Log: YYYY-MM-DD

> Session log for [Weekday], [Month] [Day], [Year]

---

## Session Notes

[Bullet-point summary of what was done]

**Docs updated this session:** [list]
```

---

## Step 6 — Update memory/MEMORY.md (repo)

File: `phase2/memory/MEMORY.md` (committed to git, source of truth for durable project facts).

Three locations to update:

1. **Logs Index table** — add a new row (or append to today's row if /log-run already added one):
   ```
   | YYYY-MM-DD | [concise one-line summary of session work] |
   ```
   If the row already exists (pipeline run was logged today), append "; [session summary]" to the existing row — do NOT add a duplicate row.

2. **Last updated** date at the bottom of the file.

3. **Key Facts section** — if any persistent facts changed (new URL, new pricing figure, new decision, new deferred item), update the relevant bullet. Do NOT add ephemeral session details to Key Facts — only durable facts belong there.

---

## Step 6b — Update external Claude memory MEMORY.md

File: `C:\Users\YYY\.claude\projects\c--Users-YYY-Omdena-Capstone-project-capstone-project-lordwalt-phase2\memory\MEMORY.md` (Claude Code session memory — NOT committed to git).

This file must be kept in sync with the repo MEMORY.md. Two locations to update:

1. **Logs Index** — add or append a bullet entry in the same format as the repo Logs Index:
   ```
   - [YYYY-MM-DD](logs/YYYY-MM-DD.md) — [concise one-line summary]
   ```
   If an entry for today already exists, append "; [session summary]" — do NOT add a duplicate.

2. **Known Bugs Fixed / Antipatterns** — if new bugs were fixed or new antipatterns were added to MEMORY.md during the session, verify they are present in the external memory too. The external memory is the canonical antipattern store.

**IMPORTANT:** Both files must be updated every session. Updating only one is a protocol violation. The repo memory is committed to git; the external memory persists in Claude Code across sessions. They serve different purposes but the Logs Index must be consistent in both.

---

## Step 7 — Commit and push

Stage all changed files. Commit message format:

```
docs(session): YYYY-MM-DD — [one-line summary of work done]
```

Then push to remote immediately.

---

## Full checklist before committing

- [ ] Git log reviewed — scope of session understood
- [ ] User confirmed any non-git context
- [ ] Only affected docs updated (no phantom edits)
- [ ] `Last Updated` dates updated on changed docs
- [ ] Daily log file created or appended
- [ ] `memory/MEMORY.md` (repo) Logs Index updated (no duplicate rows)
- [ ] `memory/MEMORY.md` (repo) Key Facts updated if durable facts changed
- [ ] `memory/MEMORY.md` (repo) Last Updated date updated
- [ ] External Claude memory Logs Index updated (same entry, bullet format)
- [ ] External Claude memory antipatterns/bugs in sync if new ones added
- [ ] Committed and pushed
