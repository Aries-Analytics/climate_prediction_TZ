# Automated Pipeline Status — March 2026

**Status**: ✅ **SHADOW RUN ACTIVE**
**Pilot**: Morogoro (Kilombero Basin)
**Version**: 4.0
**Last Updated**: March 10, 2026

> Supersedes: `docs/archive/phase3/AUTOMATED_PIPELINE_STATUS_JAN2026.md`

---

## 🚀 Shadow Run Overview

| Field | Value |
|---|---|
| **Period** | March 7, 2026 → June 5, 2026 |
| **Purpose** | Forward validation of 3–6 month forecasts against observed outcomes |
| **Schedule** | Daily 06:00 EAT (`0 6 * * *`, Africa/Dar_es_Salaam) |
| **Forecasts/run** | 12 (4 trigger types × 3 horizons) |
| **Trigger types** | drought, flood, crop_failure, heat_stress |
| **Horizons** | 3 months (primary/trigger-eligible), 4–6 months (advisory) |
| **Auto-evaluation** | ~June 8, 2026 (Brier Score computation as 3-month windows mature) |

---

## 📊 Current State (as of March 10, 2026)

| Metric | Value |
|---|---|
| `forecast_logs` rows | ~90 (12/day × days running) |
| All log status | `pending` (awaiting Jun 2026 outcome data) |
| `threshold_used` | Populated from Mar 9 onwards (0.65 drought/flood, 0.60 others) |
| `forecast_distribution` | Populated from Mar 9 onwards (horizon_tier, is_insurance_trigger_eligible, confidence bounds) |
| Probability method | CDF from physical Kilombero phase thresholds (from Mar 10 onwards) |
| Primary model | XGBoost only (R²=0.8666, 83 features) — no fallback |

---

## 🏗️ Architecture

### Scheduler (Production)
- **Container**: `climate_pipeline_scheduler_dev`
- **Image**: `docker-compose.dev.yml`
- **Server**: `root@37.27.200.227` (hewasense.majaribio.com)
- **Timezone**: Africa/Dar_es_Salaam (explicit on `CronTrigger.from_crontab()`)
- **Lock**: `pg_try_advisory_lock(123456)` on dedicated raw connection (not ORM)
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
docker restart climate_pipeline_scheduler_dev
# Confirmation: "No stale advisory locks found on startup"
```

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
| Mar 7, 2026 | Shadow run started (first correct run) |
| Mar 8, 2026 | Scheduler TZ bug fixed (UTC → EAT) |
| Mar 9, 2026 | ForecastLog.threshold_used + forecast_distribution populated |
| Mar 10, 2026 | LSTM fallback removed; CDF probability conversion deployed |
| ~Jun 8, 2026 | First Brier Score auto-evaluation (3-month windows mature) |

---

## 📈 Next Milestone

**~June 8, 2026**: The 3-month forecast windows from March 7–10 mature. The evaluator will:
1. Fetch observed climate data for Morogoro (Mar–Jun 2026)
2. Compare against forecast_logs predictions
3. Compute Brier Scores and write to `forecast_evaluations`
4. Update `forecast_logs.status` from `pending` → `evaluated`

This provides the first real forward-validation evidence for underwriter engagement.
