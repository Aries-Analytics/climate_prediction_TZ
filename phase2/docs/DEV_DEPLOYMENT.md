# Dev Deployment Guide

## Overview

This guide covers setting up and running the climate prediction pipeline in a development environment, including database configuration, Slack alerts, and monitoring.

## Prerequisites

- PostgreSQL database (local or remote)
- Python 3.8+ with all dependencies installed
- Slack workspace with webhook access (optional but recommended)
- Google Cloud Project with Earth Engine API enabled

## Environment Setup

### 1. Configure `.env` File

The `.env` file in the project root contains all configuration. Key sections:

#### Database Configuration
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/climate_dev
POSTGRES_DB=climate_dev
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password
```

**Important**: Change the default password before deploying!

#### Slack Alerts (Recommended for Dev)
```bash
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Get your webhook URL from: Slack → Apps → Incoming Webhooks

#### Logging
```bash
LOG_LEVEL=DEBUG  # Use INFO for production
LOG_FILE=logs/pipeline.log
```

### 2. Initialize Database

```bash
# Create database (if using local PostgreSQL)
createdb climate_dev

# Run migrations (if using backend app)
cd backend
alembic upgrade head

# Or initialize tables directly
python -c "from backend.app.models.climate_data import Base; from sqlalchemy import create_engine; engine = create_engine('postgresql://user:password@localhost:5432/climate_dev'); Base.metadata.create_all(engine)"
```

### 3. Test Slack Integration

```bash
# Send test notification
python -c "from utils.slack_notifier import send_test_notification; send_test_notification()"
```

You should see a test message in your Slack channel!

## Running the Pipeline

### Manual Execution

```bash
# Run full pipeline
python scripts/run_processing_pipeline.py

# Run specific data source
python -c "from modules.ingestion.chirps_ingestion import fetch_chirps_data; df = fetch_chirps_data(start_year=2020, end_year=2025); print(f'Fetched {len(df)} records')"
```

### With Mocked APIs (for testing)

```bash
# Run integration tests with mocks
pytest tests/test_ingestion_with_mocks.py -v

# Test individual mock
python -c "from tests.mocks import get_mock_chirps; mock = get_mock_chirps(); df = mock.get_data(2015, 2020); print(df.head())"
```

## Monitoring & Validation

### Check Pipeline Health

```bash
# Run health check
python scripts/monitor_pipeline_health.py

# With Slack alerts
python scripts/monitor_pipeline_health.py --send-alerts
```

Output example:
```
==============================================================
Checking Data Freshness
==============================================================
✓ Fresh      CHIRPS               Last update: 2026-01-22 (0 days ago)
✓ Fresh      NASA_POWER           Last update: 2026-01-22 (0 days ago)
⚠ Stale      ERA5                 Last update: 2026-01-15 (7 days ago)
...
Health Score: 85/100
```

### Validate Data Quality

```bash
# Validate all sources
python scripts/validate_data_quality.py

# Validate specific source
python scripts/validate_data_quality.py --source CHIRPS

# With Slack alerts
python scripts/validate_data_quality.py --send-alerts
```

### View Dev Dashboard

```bash
# Quick environment overview
python scripts/dev_dashboard_summary.py
```

Displays:
- Data sources status (freshness, record counts)
- Recent pipeline activity
- Database statistics
- Alerts configuration
- Quick action commands

## Docker Deployment (Optional)

### Using Docker Compose

```bash
# Start dev environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

## Common Tasks

### Load Historical Data

```bash
# Fetch 40-year climatology
python scripts/fetch_40_year_data.py
```

### Generate Forecasts

```bash
# Generate climate forecasts
python scripts/generate_forecasts.py
```

### Reset Data (Caution!)

```bash
# Reset forecasts only
python scripts/reset_forecasts.py

# WARNING: Never reset in production without backup!
```

## Troubleshooting

### Issue: "DATABASE_URL not set"
**Solution**: Ensure `.env` file is in the project root and contains `DATABASE_URL`

### Issue: Slack notifications not showing
**Solution**:
1. Check `ALERT_SLACK_ENABLED=true` in `.env`
2. Verify webhook URL is correct
3. Run test notification: `python -c "from utils.slack_notifier import send_test_notification; send_test_notification()"`

### Issue: Google Earth Engine authentication failed
**Solution**:
```bash
# Authenticate with GEE
earthengine authenticate

# Or set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Issue: Data appears stale
**Solution**:
1. Check recent activity: `python scripts/dev_dashboard_summary.py`
2. Run pipeline manually: `python scripts/run_processing_pipeline.py`
3. Check logs: `tail -f logs/pipeline.log`

### Issue: Import errors when running scripts
**Solution**:
```bash
# Ensure you're in project root
cd /path/to/capstone-project-lordwalt/phase2

# Install dependencies
pip install -r requirements.txt
```

## Best Practices

### Development Workflow

1. **Before coding**: Pull latest changes, check dev dashboard
2. **After changes**: Run health checks and quality validation
3. **Before commits**: Run mock integration tests
4. **Daily**: Monitor Slack alerts, check dashboard

### Data Management

- **Keep dev database separate** from production
- **Regular backups**: `pg_dump climate_dev > backup_$(date +%Y%m%d).sql`
- **Clean old test data** periodically
- **Monitor database size**: Check dashboard regularly

### Alerting Strategy

- **Dev**: Slack alerts for all issues (catch bugs early)
- **Staging**: Slack + Email for critical issues
- **Production**: Email + Slack + PagerDuty for critical

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `ALERT_SLACK_ENABLED` | Enable Slack notifications | `false` | No |
| `ALERT_SLACK_WEBHOOK_URL` | Slack webhook URL | - | If Slack enabled |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `DATA_STALENESS_THRESHOLD_DAYS` | Days before data considered stale | `7` | No |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | - | Yes (for GEE) |
| `ENVIRONMENT` | Environment name | `development` | No |

## Next Steps

1. ✅ **Setup complete** - You can now run the pipeline in dev
2. 📊 **Collect data** - Run pipeline to populate dev database
3. 🧪 **Test & iterate** - Use monitoring scripts to validate
4. 🚀 **Production prep** - When ready, create `.env.prod` with production settings

---

**Need Help?** Check the main `README.md` or monitoring guide (`docs/MONITORING_GUIDE.md`)
