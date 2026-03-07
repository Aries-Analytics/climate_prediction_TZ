# GOTCHA Framework: Agent Prompt Triggers

> This document contains reusable prompt templates to force AI agents to comply with the GOTCHA framework and its memory protocol. You can copy and paste these during your sessions.

---

## 1. The "Start of Session" Context Loader
*Use this right after you open a new chat instance to ensure the fresh agent reads the foundational rules and what the previous agent was doing.*

```markdown
Before we begin the next task, please execute your handover protocol as defined in `.agent/rules/SKILL.md`. Specifically:
1. Read `memory/MEMORY.md` to load the current system state and rules.
2. Read the daily log from today and yesterday in `memory/logs/` to catch up on recent context.
3. Read `state.json` to see our active phase.
Confirm you have loaded this context before we proceed.
```

---

## 2. The "Mid-Session Insight" Trigger
*Use this when we've just spent time debugging a weird issue, or when you make a specific technical decision you want the agent to remember (like a specific library version or configuration choice).*

```markdown
That worked. Please run `tools/memory/memory_write.py` right now to log this exact fix and the root cause into today's daily log so we don't forget it. Tag it appropriately with `--type insight`.
```

---

## 3. The "End of Session / Sprint Wrap-up" Trigger
*Use this when we've finished a major feature or solved a big ticket, right before you close out for the day.*

```markdown
We are done with this feature/sprint. Before we close out, execute the GOTCHA Sprint End protocol:
1. Synthesize all our scattered bullet points into a clean, formatted daily log for today in `memory/logs/YYYY-MM-DD.md`. Create a "Learned Behaviors" section at the bottom.
2. Extract the most critical structural facts or rules we established today and append them to `memory/MEMORY.md`. 
3. Run a `grep_search` across `docs/` to ensure no documentation files are contradicting the code we just wrote.
```

---

## 4. The "Data Leakage / Architecture Shift" Trigger
*Use this if we ever change the core ML features, thresholds, or API responses—things that break backward compatibility.*

```markdown
Since we just modified the [feature count / payout threshold / model architecture], you are mandated by GOTCHA Law #8 (Autonomous Documentation) to update the system. 
Please find and update all relevant files in `docs/current/`, `docs/references/`, `goals/`, `state.json`, and `memory/MEMORY.md` to reflect this new reality before doing anything else.
```

---

## 5. The "Global Doc Sweep & Sync" Trigger
*Use this perfectly-phrased prompt when you want to force an agent to do exactly what we did today: meticulously hunt down every stale number across the entire project and sync it to the newest truth.*

```markdown
We have a new canonical metric/fact: [e.g., XGBoost R² is now 0.8666, features are 83]. 
As per GOTCHA Law #8 (Autonomous Documentation), execute a global documentation sweep. 
1. Use `grep_search` across the `docs/current/`, `docs/references/`, `goals/`, and `memory/` directories to find all stale instances of the old metrics.
2. Systematically replace them using `multi_replace_file_content`. 
3. Do NOT modify the `docs/archive/` or `docs/reports/` folders, as they are historical.
4. Verify your work is complete by running `grep_search` again. Create a walkthrough artifact summarizing the files changed.
```
