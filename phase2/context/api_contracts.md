# API Contracts — Context Reference

> Frontend Engineer: read this before consuming any Backend endpoint.

---

## Contract Source of Truth

**Canonical sources (code is the truth, not duplicated documentation):**

- Pilot zone IDs + coordinates → `backend/app/services/risk_service.py` (`PILOT_LOCATION_IDS`), `backend/app/services/evaluation_service.py` (`PILOT_ZONE_IDS`)
- Shadow run dates + target days → `backend/app/config/shadow_run.py`
- Payout threshold → `backend/app/services/pipeline/orchestrator.py` (`_PROB_THRESHOLDS`)
- Active model → `outputs/models/active_model.json`

Frontend must consume live API responses, not hardcoded duplicates of these values.

---

## Current Pilot Values (reference snapshot — 2026-04-16)

```json
{
  "PILOT_LOCATION_IDS": [7, 8],
  "pilot_zones": {
    "7": {"name": "Ifakara TC", "lat": -8.1333, "lon": 36.6833, "farmers": 400},
    "8": {"name": "Mlimba DC",  "lat": -8.0167, "lon": 35.95,   "farmers": 600}
  },
  "payout_threshold": 0.75,
  "pilot_region": "Kilombero Basin (Ifakara TC + Mlimba DC)",
  "pilot_crop": "Rice",
  "pilot_farmers": 1000,
  "timezone": "Africa/Dar_es_Salaam (pipeline schedule); UTC (timestamps)"
}
```

> These values are a snapshot for quick reference. The running backend is the
> source of truth — if this snapshot drifts from the code, the code wins.

### Location IDs — active
- `7` = Ifakara TC (-8.1333°S, 36.6833°E, 400 farmers)
- `8` = Mlimba DC (-8.0167°S, 35.95°E, 600 farmers)

### Location IDs — deprecated / do not use for pilot
- `6` = Morogoro city — deprecated 2026-04-14 (120+ km from actual Kilombero Basin; replaced by the two-zone split)
- `1`–`5` = Arusha / Dar es Salaam / Dodoma / Mbeya / Mwanza — **training** locations, not pilot targets
- Do NOT hardcode `locationId: 1` on the frontend — this was a historical regression

### Payout Threshold
- Backend canonical: `0.75` (75%) — defined in `orchestrator.py:_PROB_THRESHOLDS`
- Frontend must not override this — display whatever the API returns
- Do NOT use `0.50` (50%) — this was a historical error

---

## Zone-aware API Endpoints (2026-04-14+)

### Evidence Pack (zone-split evaluation)
- `GET /api/v1/evidence-pack/metrics` — aggregate + per-zone Brier/RMSE/ECE
- `GET /api/v1/evidence-pack/metrics?location_id=7` — Ifakara TC only
- `GET /api/v1/evidence-pack/metrics?location_id=8` — Mlimba DC only
- `GET /api/v1/evidence-pack/basis-risk` — aggregate + per-zone NDVI proxy basis risk
- `GET /api/v1/evidence-pack/basis-risk?location_id=7|8` — zone-specific
- `GET /api/v1/evidence-pack/final-report` — GO/NO-GO gates (overall + per-zone)
- `GET /api/v1/evidence-pack/execution-log` — pipeline history + shadow run progress (live `valid_run_days`, `projected_end_date`, `gap_days`)

### Climate Data
- `GET /api/climate-data?location_id=<id>` — historical observations
- `GET /api/climate-data/latest?location_id=<id>` — most recent data point

### Forecasts
- `GET /api/forecasts?location_id=<id>` — ML-generated forecasts
- `GET /api/climate-forecasts?location_id=<id>` — seasonal forecasts
- `POST /api/forecasts/generate` — trigger forecast generation

### Trigger Events
- `GET /api/trigger-events?location_id=<id>` — insurance trigger history
- `GET /api/trigger-events/active` — currently active triggers

### Model Performance
- `GET /api/model-performance?location_id=<id>` — model accuracy metrics

### Risk / Portfolio
- `GET /api/portfolio-risk` — portfolio metrics + `shadowRunConfig` with live projected dates

---

## Error Handling Contract

When Backend returns errors, Frontend must handle gracefully:

| Status | Meaning | Frontend Response |
|--------|---------|------------------|
| 200 | Success | Render data normally |
| 404 | No data for location | Show "No data available" state, not crash |
| 422 | Invalid parameters | Show parameter error, check contract values |
| 500 | Server error | Show "Service temporarily unavailable" |
| 503 | Data source unavailable | Show "Climate data source offline" |

**NEVER** fabricate data or show cached stale data as if it were current.

---

*Last updated: 2026-04-16 — updated for two-zone Kilombero split; removed stale `state.json` reference (never wired)*
