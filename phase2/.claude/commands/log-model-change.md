# /log-model-change — Law #8 Model Change Doc Sweep

Run this after ANY model retrain, feature set change, threshold recalibration, or config change that affects reported accuracy or model behaviour. This is the GOTCHA Law #8 (AUTONOMOUS DOCUMENTATION) enforcement skill.

**CRITICAL:** Never skip this after a model change. Stale accuracy numbers in external docs are a compliance and credibility risk.

---

## Step 1 — Gather the new model facts

Collect the following before touching any doc:

```bash
# Check active model
cat outputs/models/active_model.json

# Check latest training results
cat outputs/models/latest_training_results.json

# Check feature count
python -c "import json; d=json.load(open('outputs/models/feature_selection_results.json')); print(len(d.get('selected_features', d.get('features', []))))"
```

Ask the user to confirm or provide:
- New R² (test set, single-location)
- New R² (test set, 6-location if available)
- New feature count
- What changed: retrain, feature removal, threshold update, config change?
- New model file name (if changed)
- Training date

Do NOT proceed until these facts are confirmed. Never invent or assume accuracy numbers.

---

## Step 2 — Identify what changed

Determine the scope of the change to know which docs need updating:

| Change type | Affected docs |
|---|---|
| R² / accuracy changed | ALL docs below — full sweep |
| Feature count changed | ML_MODEL_REFERENCE, EXECUTIVE_SUMMARY, MEMORY.md Key Facts |
| Threshold recalibration | PARAMETRIC_INSURANCE_FINAL, BUSINESS_CASE, KILOMBERO_BASIN_PILOT_SPECIFICATION |
| New model file name | MEMORY.md Key Facts (active_model.json note), no other docs |
| Basis risk changed | PARAMETRIC_INSURANCE_FINAL, BUSINESS_CASE, HEWASENSE_EXTERNAL_BRIEF |

---

## Step 3 — Full doc sweep (if R² changed)

Update ALL of the following. Read each file first; update ONLY the accuracy-bearing lines:

### 3a. `docs/references/ML_MODEL_REFERENCE.md`
- Model version header
- R² values (test set, all locations)
- Feature count
- Training date
- Version history table at bottom

### 3b. `docs/current/EXECUTIVE_SUMMARY.md`
- R² in Key Facts section
- Any "86.7%" or old R² references — update all instances
- `Last Updated` date

### 3c. `docs/references/PARAMETRIC_INSURANCE_FINAL.md`
- Model performance section
- Basis risk (if changed)
- `Last Updated` date

### 3d. `docs/references/HEWASENSE_EXTERNAL_BRIEF.md`
- R² / accuracy claim in system overview
- Feature count if mentioned
- `Last Updated` date

### 3e. `docs/references/BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md`
- Model accuracy section
- `Last Updated` date

### 3f. `docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md`
- Model section accuracy reference
- `Last Updated` date

### 3g. `docs/references/CRITICAL_NUMBERS_VERIFICATION.md`
- All R² / accuracy entries
- Feature count entry
- `Last Updated` date

### 3h. `memory/MEMORY.md` — Key Facts section
- Production ML model R² line
- Feature count line
- Model file name (if changed)

---

## Step 4 — Verify no stale numbers remain

After editing, run a search to confirm no old R² value survives anywhere:

```bash
# Replace OLD_R2 with the previous accuracy value (e.g. 0.8666 or 86.7)
grep -r "OLD_R2" docs/ memory/
```

If any hits remain, read those files and update them before proceeding.

---

## Step 5 — Create or update daily log file

Append to or create `memory/logs/YYYY-MM-DD.md`:

```markdown
---

## Model Change — [Month Day]

**Change:** [retrain / feature removal / threshold update / config change]
**Previous:** R²=[old], [old_features] features
**New:** R²=[new], [new_features] features, model file: [filename]
**Reason:** [why the change was made]
**Docs updated:** [list all docs updated in Step 3]
```

---

## Step 6 — Update memory/MEMORY.md Logs Index

Add or append to today's row:
```
| YYYY-MM-DD | Model change: [what changed] — R²=[old]→[new], docs swept |
```

Update `Last updated` date at the bottom.

---

## Step 7 — Commit and push

Stage all changed files. Commit message format:

```
feat(model): retrain YYYY-MM-DD — R²=[new], [N] features, Law #8 doc sweep
```

Or if threshold/config only:
```
fix(model): recalibrate [what] — Law #8 doc sweep
```

Then push to remote immediately.

---

## Full checklist before committing

- [ ] New R² confirmed from `latest_training_results.json` — NOT invented
- [ ] Feature count confirmed from `feature_selection_results.json`
- [ ] `active_model.json` updated to point to new model
- [ ] ML_MODEL_REFERENCE.md updated
- [ ] EXECUTIVE_SUMMARY.md updated (all R² instances)
- [ ] PARAMETRIC_INSURANCE_FINAL.md updated
- [ ] HEWASENSE_EXTERNAL_BRIEF.md updated
- [ ] BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md updated
- [ ] PROJECT_OVERVIEW_CONSOLIDATED.md updated
- [ ] CRITICAL_NUMBERS_VERIFICATION.md updated
- [ ] MEMORY.md Key Facts updated
- [ ] Stale number grep came back clean
- [ ] Daily log updated
- [ ] Committed and pushed
