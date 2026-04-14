# Automated Forecasting Pipeline - Deployment Guide

**Last Updated**: January 22, 2026  
**Status**: ✅ **PRODUCTION ACTIVE**  
**Version**: 1.0

> [!IMPORTANT]
> **Scheduler Enabled**: January 23, 2026 @ 23:45 EAT  
> **Next Run**: January 24, 2026 @ 06:00 AM EAT  
> **Configuration**: Daily automated execution at 6:00 AM EAT for Morogoro pilot

---

## 📋 Overview

This guide covers deploying the automated forecasting pipeline for the Tanzania Climate Prediction system.

**Current Deployment**: Morogoro Pilot (Kilombero Basin)
- **Location**: Single pilot location (Morogoro, Kilombero Basin)
- **Crop**: Rice
- **Farmers**: 1,000
- **Forecasts**: 31 per day (31-day horizon)

The pipeline runs daily at 6:00 AM EAT to:
1. Ingest fresh climate data from 5 sources
2. Validate data quality
3. Generate climate forecasts for Morogoro pilot
4. Send alerts on failures
5. Monitor system health

---

## 🎯 Pre-Deployment Checklist

### Required Infrastructure
- [ ] PostgreSQL database (v13+)
- [ ] Redis (optional, for caching)
- [ ] Docker & Docker Compose
- [ ] Slack workspace with webhook
- [ ] Email SMTP server (optional)

### Required Credentials
- [ ] Google Earth Engine Service Account (for CHIRPS/NDVI)
- [ ] NASA POWER API access (free, no key needed)
- [ ] Copernicus CDS API key (for ERA5)
- [ ] Database connection string
- [ ] Slack webhook URL

---

## 🚀 Quick Start (Docker Deployment)

### 1. Configure Environment

Copy and configure environment file:
```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/climate

# Slack Alerts
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Schedule (daily at 6 AM UTC)
PIPELINE_SCHEDULE=0 6 * * *
PIPELINE_TIMEZONE=UTC

# API Keys
GEE_SERVICE_ACCOUNT_KEY=/path/to/gee-service-account.json
ERA5_API_KEY=your_cds_api_key
```

### 2. Run Database Migrations

```bash
# Initialize database schema
docker compose run scheduler alembic upgrade head
```

### 3. Start Services

```bash
# Start all services
docker compose up -d

# Services started:
# - postgres: Database
# - scheduler: Pipeline scheduler (runs pipeline daily)
# - monitoring: Metrics and health checks
```

### 4. Verify Deployment

```bash
# Check scheduler is running
docker compose logs scheduler

# Check health endpoint
curl http://localhost:8080/health

# Check metrics endpoint
curl http://localhost:9090/metrics
```

---

## 📦 Service Architecture

### Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **scheduler** | - | Runs pipeline on schedule |
| **monitoring** | 8080, 9090 | Health checks & metrics |
| **postgres** | 5432 | Database |
| **redis** (optional) | 6379 | Caching |

### Data Flow

```
Scheduler Service
    ↓
Pipeline Orchestrator
    ↓
├── Incremental Ingestion Manager
│   ├── CHIRPS (Google Earth Engine)
│   ├── NASA POWER
│   ├── ERA5 (Copernicus)
│   ├── NDVI (Google Earth Engine)
│   └── Ocean Indices (NOAA)
    ↓
Data Quality Validator
    ↓
Forecast Generation
    ↓
Alert Service (Slack/Email)
```

---

## ⚙️ Configuration Reference

### Environment Variables

**Core Settings:**
```bash
ENVIRONMENT=production          # production, staging, development
DATABASE_URL=postgresql://...   # PostgreSQL connection string
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

**Pipeline Schedule:**
```bash
PIPELINE_SCHEDULE="0 6 * * *"              # Cron expression — 6 AM in PIPELINE_TIMEZONE
PIPELINE_TIMEZONE=Africa/Dar_es_Salaam    # Timezone for schedule (EAT = UTC+3)
ENABLE_SCHEDULER=true           # Enable/disable automatic runs
```

**Alerts:**
```bash
# Slack
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Email
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@example.com
ALERT_EMAIL_RECIPIENTS=admin@example.com
ALERT_EMAIL_USERNAME=your_email@gmail.com
ALERT_EMAIL_PASSWORD=your_app_password
```

**Data Quality Thresholds:**
```bash
DATA_STALENESS_THRESHOLD_DAYS=7         # Alert if data > 7 days old
FORECAST_STALENESS_THRESHOLD_DAYS=7     # Alert if forecasts > 7 days old
DATA_QUALITY_SCORE_THRESHOLD=0.7        # Must score 70% or higher
```

**Retry Configuration:**
```bash
RETRY_MAX_ATTEMPTS=5            # More resilient for production
RETRY_INITIAL_DELAY=3           # Seconds before first retry
RETRY_BACKOFF_FACTOR=2          # Exponential backoff multiplier
```

**Monitoring:**
```bash
MONITORING_METRICS_PORT=9090    # Prometheus metrics
MONITORING_HEALTH_PORT=8080     # Health check endpoint
ENABLE_MONITORING=true
```

---

## 🔍 Monitoring & Alerts

### Health Check Endpoint

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "last_execution": "2026-01-22T06:00:00Z",
  "next_execution": "2026-01-23T06:00:00Z",
  "pipeline_status": "idle",
  "data_sources": {
    "CHIRPS": "fresh",
    "NASA_POWER": "fresh",
    "ERA5": "fresh",
    "NDVI": "fresh",
    "OCEAN_INDICES": "fresh"
  }
}
```

### Prometheus Metrics

```bash
curl http://localhost:9090/metrics
```

**Key Metrics:**
- `pipeline_execution_duration_seconds` - How long pipeline runs take
- `pipeline_execution_status` - Success/failure counts
- `data_source_fetch_duration_seconds` - Per-source ingestion time
- `data_quality_score` - Overall data quality (0-1)
- `forecast_generation_count` - Number of forecasts generated

### Grafana Dashboard

Import provided dashboard: `monitoring/grafana-dashboard.json`

**Panels:**
- Pipeline execution timeline
- Success/failure rates
- Data quality trends
- Alert history

---

## 🛠️ Manual Operations

### Trigger Manual Run

```bash
# Using CLI
docker compose exec scheduler python -m app.cli pipeline run

# Or via API (if exposed)
curl -X POST http://localhost:8000/api/v1/pipeline/trigger
```

### Check Pipeline Status

```bash
# View current status
docker compose exec scheduler python -m app.cli pipeline status

# View execution history
docker compose exec scheduler python -m app.cli pipeline history --days 7
```

### Test Alerts

```bash
# Test Slack webhook
docker compose exec scheduler python -m app.cli pipeline test-alerts --channel slack

# Test email
docker compose exec scheduler python -m app.cli pipeline test-alerts --channel email
```

---

## 🐛 Troubleshooting

### Pipeline Not Running

**Check scheduler is running:**
```bash
docker compose ps scheduler
docker compose logs scheduler
```

**Common Causes:**
- `ENABLE_SCHEDULER=false` in `.env`
- Invalid cron expression in `PIPELINE_SCHEDULE`
- Database connection failed

**Solution:**
```bash
# Check scheduler status
docker compose logs scheduler | grep ERROR

# Restart scheduler
docker compose restart scheduler
```

### Data Ingestion Failures

**Check logs:**
```bash
docker compose logs scheduler | grep "ingestion"
```

**Common Causes:**
- API credentials expired/invalid
- Network connectivity issues
- Rate limiting

**Solution:**
```bash
# Test API connectivity
docker compose exec scheduler python -m app.services.pipeline.test_apis

# Check credentials
cat .env | grep API

# Manual retry
docker compose exec scheduler python -m app.cli pipeline run --source CHIRPS
```

### Alerts Not Delivering

**Test alert channels:**
```bash
docker compose exec scheduler python -m app.cli pipeline test-alerts
```

**Common Causes:**
- Slack webhook URL incorrect
- SMTP configuration wrong
- `ALERT_SLACK_ENABLED=false`

**Solution:**
```bash
# Verify webhook URL
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from command line"}' \
  YOUR_SLACK_WEBHOOK_URL

# Check email SMTP
telnet smtp.gmail.com 587
```

### Poor Data Quality Scores

**Check quality metrics:**
```bash
docker compose exec scheduler python scripts/validate_data_quality.py
```

**Common Causes:**
- Missing data from sources
- Out-of-range values
- Large date gaps

**Solution:**
```bash
# View quality details
docker compose exec scheduler python -c "
from app.services.pipeline.data_quality import DataQualityValidator
import pandas as pd
# Load and validate data
"

# Re-run ingestion
docker compose exec scheduler python -m app.cli pipeline run
```

---

## 📊 Production Best Practices

### Recommended Settings

**Production `.env`:**
```bash
ENVIRONMENT=production
ENABLE_SCHEDULER=true
LOG_LEVEL=INFO

# More resilient retries
RETRY_MAX_ATTEMPTS=7
RETRY_INITIAL_DELAY=5

# Stricter thresholds
DATA_STALENESS_THRESHOLD_DAYS=3
DATA_QUALITY_SCORE_THRESHOLD=0.8

# All alert channels
ALERT_SLACK_ENABLED=true
ALERT_EMAIL_ENABLED=true
```

### Monitoring Strategy

1. **Daily**: Review Grafana dashboard
2. **Weekly**: Check data quality trends
3. **Monthly**: Review execution history, optimize
4. **On Alert**: Investigate immediately

### Backup & Recovery

**Database Backups:**
```bash
# Daily backup (add to cron)
0 2 * * * docker compose exec postgres pg_dump climate > backup_$(date +\%Y\%m\%d).sql
```

**Recovery:**
```bash
# Restore from backup
docker compose exec -T postgres psql climate < backup_20260122.sql
```

---

## 🚀 Scaling Considerations

### Horizontal Scaling

Currently single-instance. To scale:

1. **Multiple scheduler instances**: Use distributed lock (Redis)
2. **Load balancing**: API endpoints behind load balancer
3. **Database**: PostgreSQL replication for reads

### Performance Optimization

**If pipeline runs slow:**
- Enable Redis caching
- Increase database connection pool
- Parallelize source ingestion
- Optimize data quality checks

**Configuration:**
```bash
DATABASE_POOL_SIZE=20
REDIS_ENABLED=true
PARALLEL_INGESTION=true
```

---

## 📚 Additional Resources

- **Architecture**: See `docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md`
- **API Documentation**: `backend/API_DOCUMENTATION.md`
- **Mock APIs (Testing)**: `tests/mocks/README.md`
- **Monitoring Guide**: `docs/MONITORING_GUIDE.md`
- **Data Pipeline Reference**: `docs/references/DATA_PIPELINE_REFERENCE.md`

---

## ✅ Post-Deployment Checklist

- [ ] All services running (`docker compose ps`)
- [ ] Health check passing (`curl http://localhost:8080/health`)
- [ ] Slack alerts delivered (`test-alerts` command)
- [ ] First manual run successful
- [ ] Grafana dashboard configured
- [ ] Database backups automated
- [ ] Documentation updated with any customizations
- [ ] Team trained on manual operations
- [ ] Runbook created for on-call

---

---

## 📋 March 2026 Updates (Shadow Run Active)

### Mar 8 — Scheduler Timezone Fix (Critical)

**Problem**: Scheduler was running at 06:00 UTC (09:00 EAT) instead of 06:00 EAT.
**Root Cause**: `CronTrigger.from_crontab()` does NOT inherit timezone from `BackgroundScheduler(timezone=...)` — it must be passed explicitly.

```python
# backend/app/services/pipeline/scheduler.py:215
# CORRECT:
trigger = CronTrigger.from_crontab(self.schedule, timezone=self.timezone)
```

**Verification**: Check scheduler logs for `+03:00` suffix on "Next scheduled run" — confirms Africa/Dar_es_Salaam is active.

### Mar 8–10 — Shadow Run Active (Mar 7 – Jun 12, 2026 revised)

The system is now in **shadow run** mode — generating forward forecasts for the Kilombero Basin (Ifakara TC + Mlimba DC) that will be evaluated against observed conditions once 3-month windows mature (~Jul 2026).

| Field | Value |
|---|---|
| Zones | Ifakara TC (id=7) + Mlimba DC (id=8) |
| Forecasts per run | 24 (3 trigger types × 4 horizons × 2 zones) |
| Schedule | Daily 06:00 EAT (`0 6 * * *`) |
| Auto-evaluation starts | ~Jul 10, 2026 (Brier Scores, per-zone + aggregate) |

### Mar 10 — Stale Advisory Lock Recovery

If the scheduler fires but logs `"lock already held"` with no prior `"Pipeline execution starting"` in the same run window, the lock is stale from a previous interrupted session.

```bash
# Recovery:
docker restart climate_pipeline_scheduler_dev
# Confirmation: "No stale advisory locks found on startup"
```

Do NOT issue `SELECT pg_advisory_unlock(123456)` manually — the startup `_clear_stale_locks()` routine handles it correctly.

### Mar 10 — Probability Conversion Update

`ForecastLog.probability_score` is now computed via physical CDF thresholds (Kilombero rice phase thresholds from TARI/FAO) rather than sigmoid. See `backend/app/services/forecast_service.py:_raw_to_probability()`.

---

**Support**: For issues, check logs first, then consult troubleshooting section.
**Maintained By**: Tanzania Climate Prediction Team
**Last Verified**: March 10, 2026
