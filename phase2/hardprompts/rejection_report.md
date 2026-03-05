# Auditor Rejection Report Template

> Use this template when blocking a merge in Auditor mode.
> Record the report in `state.json → auditor_feedback` as well.

---

## Template

```markdown
## Rejection Report — [Date]

**Merge blocked:** [branch/PR name]

### Violation 1

- **Violated Rule:** [Which project law from SKILL.md]
- **Location:** [file_path:line_number]
- **What Was Detected:** [Exact code pattern or behavior found]
- **Why It Violates Project Laws:** [Explain why this matters for HewaSense reliability]
- **Required Action:** [Specific steps for Backend Architect/Frontend Engineer to fix]
- **Verification Method:** [How this will be confirmed in the next Auditor review]

### Violation 2
(repeat as needed)

---

**Instructions for Backend Architect / Frontend Engineer:**
1. Read this rejection report
2. Switch to appropriate implementation persona
3. Address each violation in order
4. Run `python audit.py` locally to pre-check
5. Request new Auditor review when ready
```

---

## Example

```markdown
## Rejection Report — 2026-02-22

**Merge blocked:** agent/fix-ml-bridge-and-data-truth

### Violation 1

- **Violated Rule:** NO SYNTHETIC FALLBACKS
- **Location:** backend/app/services/forecast_service.py:185
- **What Was Detected:** `_baseline_prediction` still returns fabricated regional medians
- **Why It Violates:** Farmers receive predictions based on hardcoded numbers instead of ML model output
- **Required Action:** Remove `_baseline_prediction` entirely. Replace with `raise DataSourceConnectionError(...)`
- **Verification Method:** `grep -r "_baseline_prediction" backend/` returns zero matches
```
