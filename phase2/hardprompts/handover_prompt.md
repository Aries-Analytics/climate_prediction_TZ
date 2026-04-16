# Model / Session Handover Prompt Template

> Use this exact prompt when starting a fresh session or switching models.
> Adapt only the final sentence to match the active task.

---

## Template

```
I am starting a fresh session. Please initialize by reading these files in order:

1. CLAUDE.md (repo root) — auto-loaded by the harness; project instructions, personality, tools
2. .agent/rules/SKILL.md — project laws and GOTCHA layer map
3. memory/MEMORY.md — persistent facts, Key Facts section, Logs Index
4. memory/logs/YYYY-MM-DD.md for today + yesterday — session continuity
5. goals/manifest.md — find the relevant active goal workflow (if one is active)

Identify the current branch and the latest commit. If resuming a specific task,
check recent session logs for context.

Resume the task of [DESCRIBE ACTIVE TASK] without using placeholders or synthetic data.
```

---

## Example (during shadow run monitoring)

```
I am starting a fresh session. Please initialize by reading these files in order:

1. CLAUDE.md
2. .agent/rules/SKILL.md
3. memory/MEMORY.md (Key Facts + Logs Index)
4. memory/logs/2026-04-16.md and 2026-04-15.md

Identify the current branch and latest commit.

Resume monitoring the shadow run (currently in Day N of 90). Check the Evidence Pack
dashboard API (/v1/evidence-pack/execution-log) and the most recent Slack pipeline
alert. Flag any gaps or forecast count anomalies.
```

---

## Example (during feature work)

```
I am starting a fresh session. Please initialize by reading these files in order:

1. CLAUDE.md
2. .agent/rules/SKILL.md
3. memory/MEMORY.md
4. memory/logs/[yesterday].md
5. goals/feature_expansion.md

Identify the current branch and latest commit.

Resume building the new Early Warning notification feature without using placeholders
or synthetic data.
```

---

## Notes

- `state.json` was referenced in a previous version of this template as a session
  state file — it was never wired to runtime. Removed 2026-04-16.
- `args/persona_config.yaml` was referenced as "active persona, sprint phase,
  forbidden patterns" — the persona/phase fields were unread scaffolding and
  were removed 2026-04-16. The file now holds only `forbidden_patterns` and
  `test_allowed_patterns` for `scripts/audit.py`. If you need audit behaviour,
  point scripts at that file; you do not need to read it to start a session.
- `CLAUDE.md` (repo root) is the single active context file. It is auto-loaded
  by the harness on every session.
