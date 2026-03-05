# Data Ingestion — ATLAS Workflow

## Goal

Ingest, validate, and store climate data from external sources (CHIRPS, Google Earth Engine, weather stations) into HewaSense database. Ensure data quality gates prevent corrupt data from reaching the ML pipeline.

---

## App Brief (A — Architect)

- **Problem:** ML models need reliable historical and real-time climate data for training and serving.
- **User:** The ML pipeline (automated) and Backend Architect (manual verification).
- **Success:** Data passes all quality checks. No gaps > 7 days in continuous series. All values within physical bounds.
- **Constraints:** GEE API quotas, CHIRPS update frequency (~weekly), station data availability.

---

## Data Sources (T — Trace)

| Source | Data Type | Frequency | Auth | Tool |
|--------|-----------|-----------|------|------|
| CHIRPS | Rainfall | 5-day pentad | No auth | `backend/scripts/fetch_chirps_data.py` |
| Google Earth Engine | NDVI, LST | ~16 day | OAuth/Service Account | `backend/scripts/fetch_gee_data.py` |
| Weather Stations | Temp, humidity | Daily | API key | `backend/scripts/fetch_station_data.py` |

### Quality Gates

Before any data is committed to database:
- Precipitation: 0 ≤ value ≤ 500 mm/day
- Temperature: -10°C ≤ value ≤ 55°C
- NDVI: -1.0 ≤ value ≤ 1.0
- No duplicate timestamps per location
- All timestamps UTC-aware

---

## Validation (L — Link)

```
[ ] Data source API accessible
[ ] API credentials in .env and working
[ ] Database connection active
[ ] Target table schema matches expected columns
[ ] Previous ingestion log reviewed for known issues
```

---

## Execution (A — Assemble)

**Persona: Backend Architect**

1. Fetch raw data from source
2. Apply quality gate filters
3. Transform to standard schema (UTC timestamps, standard units)
4. Upsert to database (smart upsert — no duplicates)
5. Log ingestion metrics: records fetched, passed QA, rejected, inserted

---

## Verification (S — Stress-test)

```
[ ] Data appears in database with correct timestamps
[ ] No values outside physical bounds
[ ] No duplicate records created
[ ] Ingestion log shows expected counts
[ ] Downstream queries (forecast service) can read new data
```

---

## Related Files

- **Tools:** `backend/scripts/fetch_chirps_data.py`, `backend/scripts/load_calibrated_data.py`
- **Context:** `context/hewasense_domain.md` (data source details)
