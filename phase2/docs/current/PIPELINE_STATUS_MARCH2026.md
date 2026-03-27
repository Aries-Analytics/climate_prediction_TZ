# Automated Pipeline Status — March 2026

**Status**: ✅ **SHADOW RUN ACTIVE**
**Pilot**: Morogoro (Kilombero Basin)
**Version**: 4.0
**Last Updated**: March 27, 2026

> Supersedes: `docs/archive/phase3/AUTOMATED_PIPELINE_STATUS_JAN2026.md`

---

## 🚀 Shadow Run Overview

| Field | Value |
|---|---|
| **Period** | March 7, 2026 → **June 12, 2026** (revised — 7 missed days compensated) |
| **Target** | 90 valid run-days = **1,080 ForecastLog entries** (12/day) |
| **Purpose** | Forward validation of 3–6 month forecasts against observed outcomes |
| **Schedule** | Daily 06:00 EAT (`0 6 * * *`, Africa/Dar_es_Salaam) |
| **Forecasts/run** | 12 (3 trigger types × 4 horizons) |
| **Trigger types** | drought, flood, crop_failure *(heat_stress excluded — pending dedicated temperature model)* |
| **Horizons** | 3–4 months = **primary** (payout-eligible, ≥75%) / 5–6 months = **advisory** (early warning, ≥50%) |
| **Auto-evaluation** | ~June 9, 2026 (Brier Score computation as first 3-month windows from Mar 9 mature) |

---

## 📊 Current State (as of March 24, 2026)

| Metric | Value |
|---|---|
| `forecast_logs` rows | 168 (14 valid run-days: Mar 11, 15–27) |
| Valid run-days achieved | 14 of 90 target (15.6%) |
| Missed days (total) | **7** — Mar 7 (late start), Mar 8 (TZ bug), Mar 9–10 (ForecastLog not generated), Mar 12–14 (stale lock) |
| All log status | `pending` (validity windows 3–6 months ahead) |
| `threshold_used` | Populated from Mar 9 onwards (0.65 drought/flood, 0.60 others) |
| `forecast_distribution` | Populated from Mar 9 onwards (horizon_tier, is_insurance_trigger_eligible, confidence bounds) |
| Probability method | CDF from physical Kilombero phase thresholds (from Mar 10 onwards) |
| Primary model | XGBoost only (R²=0.8666, 83 features) — no fallback |
| Payout calculation | ✅ Fixed Mar 15 — advisory tier excluded, deduplication enforced (MAX prob per triggerType×month) |

---

## 🏗️ Architecture

### Scheduler (Production)
- **Container**: `climate_pipeline_scheduler_dev`
- **Image**: `docker-compose.dev.yml`
- **Server**: `root@37.27.200.227` (hewasense.majaribio.com)
- **Timezone**: Africa/Dar_es_Salaam (explicit on `CronTrigger.from_crontab()`)
- **Lock**: `pg_try_advisory_lock(123456)` on dedicated **NullPool** connection — NullPool mandatory, QueuePool leaks session-level advisory locks
- **Job store**: In-memory (not persistent — prevents phantom runs after restarts)

### Forecast Generation
- **Model**: XGBoost (`xgboost_climate.pkl`) — primary only, no fallback
- **Features**: 83 (from `feature_selection_results.json`)
- **Probability**: `_raw_to_probability()` — CDF from Kilombero rice phase thresholds (TARI/FAO)
- **Lookback**: 7 months from today `.replace(day=1)` for ≥6 monthly records

### ForecastLog Fields (Evidence Pack)
| Field | Source | Notes |
|---|---|---|
| `probability_score` | `_raw_to_probability()` | Phase-aware CDF, not sigmoid |
| `threshold_used` | `_PROB_THRESHOLDS` in orchestrator | 0.65 drought/flood, 0.60 others |
| `forecast_distribution` | `get_horizon_tier()` | horizon_tier + is_insurance_trigger_eligible |
| `status` | Set at creation | `pending` until evaluated |

---

## 🔧 Operational Runbook

### Check pipeline ran successfully
```bash
ssh hewasense "docker logs climate_pipeline_scheduler_dev --tail 20 2>&1"
# Look for: "Scheduled execution completed: success"
```

### Stale advisory lock (run skipped)
```bash
# Symptom: "lock already held" with no prior "Pipeline execution starting"
# Step 1: identify and kill the zombie Postgres session
docker exec climate_db_dev psql -U user -d climate_dev -c \
  "SELECT pg_terminate_backend(a.pid) FROM pg_stat_activity a JOIN pg_locks l ON a.pid=l.pid WHERE l.locktype='advisory' AND l.objid=123456;"
# Step 2: restart scheduler so _clear_stale_locks() runs on startup
docker compose -f docker-compose.dev.yml restart pipeline-scheduler
# Confirmation: "No stale advisory locks found on startup"
```
**Root cause (permanent fix deployed Mar 15):** `acquire_lock()` now uses `NullPool` — ensures `connection.close()` truly terminates the Postgres session. `release_lock()` calls `pg_advisory_unlock` explicitly before dispose.

### Check forecast_logs count
```bash
ssh hewasense "docker exec climate_db_dev psql -U user -d climate_dev -c 'SELECT COUNT(*), status FROM forecast_logs GROUP BY status;'"
```

### DB Wipe Recovery (emergency only)
```bash
docker exec climate_backend_dev python init_db.py
docker exec climate_backend_dev python scripts/seed_users.py
docker exec climate_backend_dev python scripts/seed_models_and_forecasts.py
# Then restore master_dataset.csv
```

---

## 📅 Key Milestones

| Date | Event |
|---|---|
| Jan 22, 2026 | Automated scheduler first deployed |
| Mar 7, 2026 | Shadow run nominal start (partial — ForecastLog not generated) |
| Mar 8, 2026 | Scheduler TZ bug fixed (UTC → EAT) |
| Mar 9, 2026 | ForecastLog.threshold_used + forecast_distribution populated |
| Mar 10, 2026 | LSTM fallback removed; CDF probability conversion deployed |
| Mar 11, 2026 | First valid run — 12 ForecastLog entries generated |
| Mar 12–14, 2026 | Stale advisory lock blocked 3 runs |
| Mar 15, 2026 | NullPool advisory lock fix; payout double-counting fixed (advisory tier excluded, dedup enforced); shadow run end extended to Jun 12 |
| ~Jun 9, 2026 | First Brier Score auto-evaluation (3-month windows from Mar 9 mature) |
| Jun 12, 2026 | Shadow run target completion (90 valid run-days = 1,080 entries) |

---

## 📈 Next Milestone

**~June 9, 2026**: The 3-month forecast windows from the first valid run (Mar 9) mature. The evaluator will:
1. Fetch observed climate data for Morogoro (Mar–Jun 2026)
2. Compare against forecast_logs predictions
3. Compute Brier Scores and write to `forecast_evaluations`
4. Update `forecast_logs.status` from `pending` → `evaluated`

**June 12, 2026**: Shadow run target completion — 90 valid run-days, 1,080 ForecastLog entries.

**Late June 2026**: Go-Live Decision — evidence pack (metrics.json + logs_export.csv + compliance statement) compiled and reviewed against Brier Score < 0.25 AND Basis Risk < 30% gate criteria. This provides the first real forward-validation evidence for TIRA submission and underwriter engagement.
