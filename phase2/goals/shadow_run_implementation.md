# Shadow-Run Simulation Implementation
## Phase 4.0 (Commercial Pilot Prep)

## Goal
Implement a live "shadow-run" (forward-testing, no-payout) simulation for the Kilombero Basin pilot. The system must issue daily, version-controlled forecasts, track them against later observations, and generate "Predicted vs Actual" performance metrics and evidence packs to prove operational reliability and calibrate basis risk for reinsurers.

---

## App Brief (A — Architect)

- **Problem:** Reinsurers need forward-tested evidence of reliability, not just historical backtesting, before committing risk capital.
- **User:** Reinsurers, Underwriters, internal Pilot Operations Team.
- **Success:** 90 days of daily forecasts successfully generated, tracked, evaluated against observations, and exportable as cryptographic/versioned evidence packs.
- **Constraints:** Must not trigger actual payouts. Must precisely track model versions, data snapshots, and prediction lead times to ensure zero look-ahead bias.

---

## Design Phase (T — Trace)

1. **Data Schema** — Create a robust `forecast_logs` schema to store `issued_at`, `valid_from`, `valid_until`, `model_version`, `forecast_value`, and `threshold_used` for every prediction.
2. **API Contracts** — 
   - New endpoint: `GET /api/v1/evaluations`
   - New endpoint: `POST /api/v1/evidence-pack`
3. **Integration Map** — Connect the existing forecast generation engine to the new logging schema.
4. **Evaluation Engine** — Build continuous "Predicted vs Actual" logic calculating Brier Score, Calibration Error, and precision/recall metrics.

---

## Build Phase (A — Assemble)

**Persona: Backend Architect / Frontend Engineer**

1. Define and implement `forecast_logs` storage and validation JSON schema.
2. Build the evaluation module (metrics: Brier, RMSE/MAE, Confusion Matrix).
3. Create the automated Evidence Pack Zip Generator API.
4. Update the React Dashboard ("Ops Summary", "Predicted vs Actual" charts).

---

## Verification Phase (S — Stress-test)

**Persona: Auditor**

- [x] End-to-end simulated run works without actual fund disbursement. *(March 4, 2026 — 12 forecasts generated per run)*
- [x] `forecast_logs` capture exact model versions and timestamps. *(ForecastLog entries saved with model_version="xgboost_v4")*
- [x] Evaluation metrics cleanly match stored mock observations. *(Backend Phase 3 complete: evaluation_service.py calculates Brier, RMSE, and Confusion Matrix. Observation backfill API is live.)*
- [x] PDF/Zip evidence packs generate successfully. *(Backend Phase 3 complete: `POST /api/v1/evidence-pack/generate` live.)*
- [ ] Dashboard displays the calibration reliability diagrams properly. *(Frontend Integration Pending)*

### Pipeline Pre-Launch Testing Results (March 4, 2026)

Pipeline fully tested and validated. Ready for shadow-run activation.
Switch schedule from `*/30 * * * *` (testing) to `0 3 * * *` (daily 6 AM EAT) to begin shadow run.

| Component | Status | Notes |
|-----------|--------|-------|
| **Scheduler** | ✅ Operational | APScheduler + SQLAlchemy job store, `max_instances=1` |
| **Data Ingestion** | ✅ All 5 sources | CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices |
| **Model Loading** | ✅ `xgboost_climate.pkl` | 77 features, R²=0.840, verified at load time |
| **Forecast Generation** | ✅ 12 per run | 3 triggers × 4 horizons × Morogoro |
| **Slack Alerts** | ✅ Working | Lock contention alerts suppressed |
| **ForecastLog** | ✅ Shadow-run logging | Evidence snapshots saved per run |

### Phase Completion Status (March 4, 2026)

| Phase | Subtask | Status | Location |
|-------|---------|--------|----------|
| **Phase 1** | Rich Slack Alerts & Metrics Fixes | ✅ Completed | `alert_service.py`, `scheduler.py`, `orchestrator.py` |
| **Phase 2** | Forecast Logs API | ✅ Completed | `api/forecast_logs.py` (`GET /`, `GET /summary`) |
| **Phase 3** | Evaluation Engine & Evidence Packs | ✅ Completed | `evaluation_service.py`, `generator.py`, `api/evidence.py` |
| **Phase 4** | React Dashboard Integration | ❌ Pending | Frontend (`Predicted vs Actual` charts, API hooks) |
