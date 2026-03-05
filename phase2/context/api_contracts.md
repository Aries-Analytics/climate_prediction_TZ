# API Contracts — Context Reference

> Frontend Engineer: read this before consuming any Backend endpoint.

---

## Contract Source of Truth

**Canonical source:** `state.json → shared_contract`

Frontend must consume these values exactly. Never override or hardcode alternatives.

---

## Shared Contract Values

```json
{
  "PILOT_LOCATION_ID": 6,
  "payout_threshold": 0.75,
  "pilot_region": "Morogoro (Kilombero Basin)",
  "pilot_crop": "Rice",
  "pilot_farmers": 1000,
  "timezone": "UTC"
}
```

### Location IDs
- `6` = Morogoro / Kilombero Basin (active pilot)
- Do NOT use `locationId: 1` — this was a historical error

### Payout Threshold
- Backend canonical: `0.75` (75%)
- Frontend must match this exactly
- Do NOT use `0.50` (50%) — this was a historical error

---

## API Endpoints

### Climate Data
- `GET /api/climate-data?location_id=6` — historical observations
- `GET /api/climate-data/latest?location_id=6` — most recent data point

### Forecasts
- `GET /api/forecasts?location_id=6` — ML-generated forecasts
- `GET /api/climate-forecasts?location_id=6` — seasonal forecasts
- `POST /api/forecasts/generate` — trigger forecast generation

### Trigger Events
- `GET /api/trigger-events?location_id=6` — insurance trigger history
- `GET /api/trigger-events/active` — currently active triggers

### Model Performance
- `GET /api/model-performance?location_id=6` — model accuracy metrics

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

*Last updated: 2026-02-22*
