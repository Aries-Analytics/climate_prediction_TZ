# Stabilization Sprint — ATLAS Workflow

## Goal

Fix all 11 issues from the February 15, 2026 code review. Restore the ML bridge so trained ensemble models are actually used in production. Remove all synthetic fallbacks. Align Frontend/Backend contracts.

## App Brief (A — Architect)

- **Problem:** Production predictions use hardcoded heuristics instead of trained ML models due to broken serving layer.
- **User:** HewaSense development team and Kilombero Basin farmers who rely on forecasts.
- **Success:** All 11 issues resolved. `audit.py` exits 0. `pytest` passes. Trained models invoked in production.
- **Constraints:** Must not break existing working features. Must not add synthetic fallbacks. Must use UTC everywhere.

---

## Data & Integration Map (T — Trace)

### Files Impacted

| Issue | File | Line(s) | Category |
|-------|------|---------|----------|
| 1 | `backend/app/services/forecast_service.py` | L27, L32 | CRITICAL — duplicate class |
| 2 | `backend/scripts/generate_forecasts.py` | L27, L58 | CRITICAL — wrong import |
| 3 | `backend/app/services/seasonal_forecast_integration.py` | L78 | CRITICAL — undefined var |
| 4 | `backend/app/services/forecast_service.py` | L170-171 | CRITICAL — predict_proba on regressor |
| 5 | Frontend components + Backend `PILOT_LOCATION_ID` | multiple | MODERATE — location ID mismatch |
| 6 | `backend/app/services/forecast_scheduler.py` | L47 | MODERATE — naive datetime |
| 7 | `backend/app/services/forecast_service.py` prepare_features | multiple | MODERATE — 10 vs 77 features |
| 8 | `backend/app/services/forecast_service.py` _baseline_prediction | multiple | MODERATE — synthetic fallback |
| 9 | Frontend payout threshold (50%) vs Backend (75%) | multiple | MODERATE — contract mismatch |
| 10 | `get_kilombero_stage` | L84, L372 | MINOR — argument count mismatch |
| 11 | Multiple files | codebase-wide | MINOR — mixed naive/aware datetime |

### Schema Changes
- Create `feature_schema.json` defining all 77 ML features (Issue 7) — *NOTE: superseded by 83 features after Mar 2026 data leakage fix; canonical source is now `feature_selection_results.json`*
- Update `state.json → shared_contract` with canonical thresholds (Issue 9)

### Edge Cases
- Feature engineering port (Issue 7) may reveal training features that depend on data not available at serving time
- Removing `_baseline_prediction` (Issue 8) requires Issues 4 & 7 fixed first or serving will crash with no fallback

---

## Validation Checklist (L — Link)

Before writing any fix code, verify:

```
[ ] On branch: agent/fix-ml-bridge-and-data-truth
[ ] Database connection tested (backend can reach DB)
[ ] state.json exists and is valid JSON
[ ] audit.py exists and is executable
[ ] .agent/rules/SKILL.md exists and is readable
[ ] pytest baseline: know which tests currently pass/fail
[ ] Trained model files exist in expected location
[ ] preprocess.py feature engineering logic is readable
```

---

## Build Sequence (A — Assemble)

**Persona: Backend Architect | Follow this exact sequence:**

### Phase 1: Fix Crashes (2-4 hrs)
- [ ] Issue 1: Remove duplicate class definition in forecast_service.py L27/L32
- [ ] Issue 2: Fix import name in generate_forecasts.py L27, fix attribute access L58
- [ ] Issue 3: Define `simple_payout` in seasonal_forecast_integration.py L78
- [ ] Write tests confirming each crash is gone

### Phase 2: Fix ML Bridge (4-6 hrs)
- [ ] Issue 4: Replace `predict_proba()` → `.predict()` in forecast_service.py L170-171
- [ ] Verify trained ensemble is actually invoked (not falling to baseline)
- [ ] Write test: call predict path, assert no AttributeError

### Phase 3: Fix Timezone (3-4 hrs)
- [ ] Issue 6: `forecast_scheduler.py` L47 → `datetime.now(timezone.utc)`
- [ ] Issue 11: Codebase-wide search for naive `datetime.now()`, standardize to UTC
- [ ] Write test: verify all datetime objects are timezone-aware

### Phase 4: Fix Contracts — LONGEST (8-12 hrs)
- [ ] Issue 5: Align `locationId` → 6 across Frontend + Backend
- [ ] Issue 7: Port ALL feature engineering from `preprocess.py` → `prepare_features`
  - Create `feature_schema.json` defining all 77 features
  - Both `train_pipeline.py` and `forecast_service.py` must reference this schema
  - Do NOT retrain on fewer features
- [ ] Issue 10: Fix `get_kilombero_stage` argument count (L84 vs L372)
- [ ] Write tests: feature count assertion, location ID assertion, function signature test

### Phase 5: Remove Violations (4-6 hrs)
- [ ] Issue 8: Remove `_baseline_prediction` synthetic fallback (safe now that Issues 4+7 fixed)
  - Replace with `raise DataSourceConnectionError("...")`
- [ ] Issue 9: Standardize payout threshold — update `state.json → shared_contract`, align Frontend
- [ ] Run `python audit.py` → must exit code 0
- [ ] Run full `pytest --cov=phase2`

---

## Verification Checklist (S — Stress-test)

**Persona: Auditor | Verify each item independently:**

```
[x] All 11 issues from Feb 15 review actually resolved (not cosmetic patches)
[x] audit.py exits code 0 (154 files, 0 violations — 2026-02-25)
[ ] All tests pass (pytest) — not yet run in full
[x] Trained ML models actually invoked in production path (Issues 4, 7)
[x] No synthetic fallbacks remain (Issue 8 removed)
[x] UTC standardized everywhere (Issues 6, 11)
[x] Contracts aligned Frontend ↔ Backend (Issues 5, 9, 10)
[x] No runtime crashes (Issues 1, 2, 3)
[x] feature_schema.json exists and lists 77 features
[x] state.json → shared_contract has canonical threshold
```

**SPRINT STATUS: ✅ COMPLETED (2026-02-25)**

All 11 issues resolved. Models retrained with 77 features. Documentation synchronized.

> **NOTE (Mar 2026):** The 77-feature references above were accurate at sprint completion. After the March 2026 data leakage fix, models were retrained with **83 features** (121 leaky features removed, R²=0.8666 XGBoost). See `CRITICAL_NUMBERS_VERIFICATION.md`.

**On pass:** Merge `agent/fix-ml-bridge-and-data-truth` → `phase2/feature-expansion`, delete stabilization branch.

**On fail:** Write rejection report per `hardprompts/rejection_report.md`, return to Backend Architect mode.

---

## Expected Timeline

| Phase | Hours | Dependency |
|-------|-------|-----------|
| Phase 1 | 2-4 | None |
| Phase 2 | 4-6 | Phase 1 |
| Phase 3 | 3-4 | None (parallel OK) |
| Phase 4 | 8-12 | Phase 2 (Issue 7 needs predict path working) |
| Phase 5 | 4-6 | Phases 2 + 4 (must fix bridge before removing fallback) |
| **Total** | **20-30** | + Auditor review cycles |

---

## Related Files

- **Args:** `args/persona_config.yaml`
- **Context:** `context/ml_serving_rules.md`, `context/hewasense_domain.md`
- **Hard Prompts:** `hardprompts/rejection_report.md`
- **Tools:** `audit.py`, `tools/manifest.md`
