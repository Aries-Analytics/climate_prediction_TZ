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
- [x] Dashboard displays the calibration reliability diagrams properly. *(Frontend Integration Complete)*

### Pipeline Pre-Launch Testing Results (March 4, 2026)

Pipeline fully tested and validated. **Shadow run v1 ran 2026-03-07 to 2026-04-13 (archived — Morogoro city coordinates, 120+ km from basin).**

**Shadow run v2 RESTARTED 2026-04-14 — two-zone Kilombero Basin split.**
Deployed to `root@37.27.200.227` on `phase2/feature-expansion`. Schedule: `0 6 * * *` (Africa/Dar_es_Salaam = 6 AM EAT). Target end: 2026-07-13 (90 days).

| Component | Status | Notes |
|-----------|--------|-------|
| **Scheduler** | ✅ Operational | APScheduler + in-memory job store, `max_instances=1` |
| **Data Ingestion** | ✅ All 5 sources | CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices — now for 2 zones |
| **Model Loading** | ✅ `xgboost_climate.pkl` | 83 features, R²=0.8666 (data leakage fix), verified at load time |
| **Forecast Generation** | ✅ 24 per run | 3 triggers × 4 horizons × 2 zones (Ifakara TC + Mlimba DC) |
| **Pilot Zones** | ✅ Two-zone | Ifakara TC (id=7, -8.13°S 36.68°E, 400 farmers) + Mlimba DC (id=8, -8.02°S 35.95°E, 600 farmers) |
| **Slack Alerts** | ✅ Working | Lock contention alerts suppressed |
| **ForecastLog** | ✅ Shadow-run logging | Evidence snapshots saved per run; auto-evaluated after validity window closes (Stage 3) |

### Phase Completion Status (March 4, 2026)

| Phase | Subtask | Status | Location |
|-------|---------|--------|----------|
| **Phase 1** | Rich Slack Alerts & Metrics Fixes | ✅ Completed | `alert_service.py`, `scheduler.py`, `orchestrator.py` |
| **Phase 2** | Forecast Logs API | ✅ Completed | `api/forecast_logs.py` (`GET /`, `GET /summary`) |
| **Phase 3** | Evaluation Engine & Evidence Packs | ✅ Completed | `evaluation_service.py`, `generator.py`, `api/evidence.py` |
| **Phase 4** | React Dashboard Integration | ✅ Completed | Frontend (`Predicted vs Actual` charts, API hooks) |

### Future Enhancements (Post-Deployment)
- [ ] **Dynamic Slack Routing**: Update `alert_service.py` to route to two different channels in reality. This requires modifying the service to accept two different webhook URLs (e.g., `SLACK_WEBHOOK_DAILY` and `SLACK_WEBHOOK_ALERTS`), or updating the JSON payload to dynamically include `"channel": "#climate-pipeline-daily"`. (Deferred: Can be hot-swapped after server deployment via GitHub pull).
