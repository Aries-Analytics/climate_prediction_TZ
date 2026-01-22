# Monitoring & Observability Guide

## Overview

Comprehensive guide for monitoring the climate prediction pipeline health, data quality, and performance.

## Monitoring Tools

### 1. Pipeline Health Monitor
**Script**: `scripts/monitor_pipeline_health.py`

Checks:
- ✅ Data freshness (how recent is the data?)
- ✅ Data completeness (do we have all expected records?)
- ✅ Basic data quality (null values, basic validation)

**Usage:**
```bash
# Run health check
python scripts/monitor_pipeline_health.py

# With Slack alerts
python scripts/monitor_pipeline_health.py --send-alerts
```

**Output Example:**
```
==============================================================
Checking Data Freshness
==============================================================
✓ Fresh      CHIRPS               Last update: 2026-01-22 (0 days ago)
✓ Fresh      NASA_POWER           Last update: 2026-01-22 (0 days ago)
⚠ Stale      ERA5                 Last update: 2026-01-15 (7 days ago)
✓ Fresh      NDVI                 Last update: 2026-01-22 (0 days ago)
✓ Fresh      OCEAN_INDICES        Last update: 2026-01-21 (1 days ago)

Health Score: 85/100
```

**Thresholds** (configurable in `.env`):
- Fresh: ≤ 7 days old
- Stale: 7-14 days old
- Very Stale: > 14 days old

### 2. Data Quality Validator
**Script**: `scripts/validate_data_quality.py`

Checks:
- ✅ Data ranges (are values realistic?)
- ✅ Missing values (how much data is missing?)
- ✅ Outliers (are there suspicious values?)
- ✅ Temporal consistency (are there large gaps?)

**Usage:**
```bash
# Validate all sources
python scripts/validate_data_quality.py

# Validate specific source
python scripts/validate_data_quality.py --source CHIRPS

# With alerts
python scripts/validate_data_quality.py --send-alerts
```

**Expected Ranges:**
- **CHIRPS Rainfall**: 0-800 mm/month (typical max: 500mm)
- **Temperature**: 10-45°C (typical: 20-35°C)
- **Humidity**: 0-100%
- **NDVI**: 0-1
- **ONI**: -3 to +3
- **IOD**: -2 to +2

### 3. Dev Dashboard
**Script**: `scripts/dev_dashboard_summary.py`

Quick overview of dev environment:
- 📊 Data sources status
- 📈 Recent activity
- 💾 Database statistics
- 🔔 Alerts configuration
- ⚡ Quick action commands

**Usage:**
```bash
python scripts/dev_dashboard_summary.py
```

## Slack Alerts Configuration

### Setup Slack Webhook

1. **Create incoming webhook** in Slack:
   - Go to your Slack workspace
   - Navigate to Apps → Incoming Webhooks
   - Create new webhook for your channel (e.g., `#climate-pipeline-dev`)
   - Copy webhook URL

2. **Configure in `.env`**:
   ```bash
   ALERT_SLACK_ENABLED=true
   ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

3. **Test integration**:
   ```bash
   python -c "from utils.slack_notifier import send_test_notification; send_test_notification()"
   ```

### Alert Types

#### 1. Pipeline Status Alerts
Sent after pipeline runs:
- ✅ **Success**: All sources fetched successfully
- ⚠️ **Partial**: Some sources had warnings
- ❌ **Failed**: Pipeline encountered errors

**Format:**
```
✅ Pipeline Run Completed Successfully

Data Sources Processed:
• CHIRPS: 1,200 records
• NASA_POWER: 1,800 records
...

Total Records: 8,500
Duration: 45.2 seconds
```

#### 2. Error Alerts
Sent when errors occur:
- API failures
- Database errors
- Processing exceptions

**Format:**
```
❌ Error: APIError (CHIRPS)

Error Message:
Connection timeout to Earth Engine API

Stack Trace:
[truncated stack trace]
```

#### 3. Data Quality Alerts
Sent when quality issues detected:
- High missing value percentage
- Excessive outliers
- Suspicious data ranges

**Format:**
```
⚠️ Data Quality Issue: CHIRPS

Issue Type: Missing Data
Details: 12% missing values (threshold: 10%)
Affected Records: 456
```

### Alert Severity Levels

| Level | Color | Icon | Use Case |
|-------|-------|------|----------|
| **INFO** | Green | ℹ️ | Informational messages |
| **SUCCESS** | Green | ✅ | Successful operations |
| **WARNING** | Orange | ⚠️ | Issues requiring attention |
| **ERROR** | Red | ❌ | Failures requiring action |
| **CRITICAL** | Dark Red | 🚨 | Severe issues requiring immediate action |

## Monitoring Best Practices

### Daily Monitoring

```bash
# Morning routine (5 minutes)
1. Check dev dashboard
   python scripts/dev_dashboard_summary.py

2. Review Slack alerts from overnight pipeline runs

3. Validate data quality if alerts present
   python scripts/validate_data_quality.py --source <FLAGGED_SOURCE>
```

### Weekly Monitoring

```bash
# Weekly health check (15 minutes)
1. Run comprehensive health check
   python scripts/monitor_pipeline_health.py --send-alerts

2. Validate all data sources
   python scripts/validate_data_quality.py --send-alerts

3. Review database size and performance
   # Check dashboard for DB size trends

4. Clean up old test data if needed
```

### Response Procedures

#### 🟢 Health Score 90-100 (Excellent)
**Action**: None required, routine monitoring

#### 🟡 Health Score 75-89 (Good)
**Action**: 
- Review warnings in Slack
- Check stale data sources
- Plan data refresh if needed

#### 🟠 Health Score 50-74 (Fair)
**Action**:
- Investigate issues immediately
- Run data quality validation
- Fix data gaps or quality issues
- Re-run pipeline if needed

#### 🔴 Health Score < 50 (Poor)
**Action**:
- **Immediate investigation required**
- Check logs: `tail -f logs/pipeline.log`
- Verify API connectivity
- Check database connection
- Alert team if needed

### Alert Fatigue Prevention

To avoid overwhelming alerts:

1. **Use appropriate thresholds**:
   ```bash
   # Dev: More permissive (catch issues early)
   DATA_STALENESS_THRESHOLD_DAYS=7
   DATA_QUALITY_MISSING_THRESHOLD=0.10
   
   # Production: Stricter
   DATA_STALENESS_THRESHOLD_DAYS=3
   DATA_QUALITY_MISSING_THRESHOLD=0.05
   ```

2. **Alert batching**: Group related alerts
3. **Scheduled reports**: Daily summaries instead of every run
4. **Alert channels**: Separate dev/staging/prod channels

## Performance Monitoring

### Key Metrics to Track

1. **Ingestion Duration** (per source)
   - Target: < 5 minutes per source
   - Alert: > 10 minutes

2. **API Response Times**
   - Target: < 10 seconds
   - Alert: > 30 seconds

3. **Database Write Performance**
   - Target: > 1000 records/second
   - Alert: < 100 records/second

4. **Data Freshness**
   - Target: Updated daily
   - Alert: > 7 days stale

### Debugging Data Issues

#### Issue: Data Appears Wrong
```bash
# 1. Check recent ingestion
python scripts/dev_dashboard_summary.py

# 2. Validate data quality
python scripts/validate_data_quality.py --source <SOURCE>

# 3. Query database directly
psql climate_dev -c "SELECT * FROM climate_data WHERE source='CHIRPS' ORDER BY date DESC LIMIT 10;"

# 4. Check logs for errors
tail -100 logs/pipeline.log | grep ERROR
```

#### Issue: Missing Data
```bash
# 1. Check data completeness
python scripts/monitor_pipeline_health.py

# 2. Identify gaps
psql climate_dev -c "
  SELECT source, MIN(date) as earliest, MAX(date) as latest, COUNT(*) as records
  FROM climate_data
  GROUP BY source;
"

# 3. Re-run ingestion for specific period
python -c "
from modules.ingestion.chirps_ingestion import fetch_chirps_data
df = fetch_chirps_data(start_year=2023, end_year=2024)
print(f'Fetched {len(df)} records')
"
```

#### Issue: Alerts Not Arriving
```bash
# 1. Check Slack config
grep SLACK .env

# 2. Test notification
python -c "from utils.slack_notifier import send_test_notification; send_test_notification()"

# 3. Check logs for errors
tail -50 logs/pipeline.log | grep -i slack

# 4. Verify webhook URL is correct
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from command line"}' \
  YOUR_WEBHOOK_URL
```

## Grafana Dashboards (Optional)

If using `docker-compose.monitoring.yml`:

### Access Grafana
- URL: http://localhost:3000
- Default credentials: admin/admin (change on first login)

### Pre-built Dashboards
1. **Pipeline Health** - Overall system health metrics
2. **Data Sources** - Per-source statistics
3. **Performance** - Ingestion and processing times
4. **Alerts** - Alert history and trends

## Log Management

### Log Locations
```
logs/pipeline.log          # Main pipeline log
logs/ingestion.log         # Data ingestion logs
logs/processing.log        # Data processing logs
backend/logs/api.log       # Backend API logs
```

### Useful Log Commands
```bash
# Tail main log
tail -f logs/pipeline.log

# Search for errors
grep ERROR logs/pipeline.log

# Filter by date
grep "2026-01-22" logs/pipeline.log

# Count errors by type
grep ERROR logs/pipeline.log | cut -d':' -f3 | sort | uniq -c | sort -rn

# Last 100 lines with context
tail -100 logs/pipeline.log
```

## Troubleshooting Guide

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Stale data | Pipeline not running | Run `python scripts/run_processing_pipeline.py` |
| High missing values | API issues | Check logs, retry ingestion |
| Outliers detected | Legitimate extreme event or data quality issue | Investigate manually |
| Slack alerts not working | Webhook misconfigured | Verify URL, test with curl |
| Health score dropping | Multiple small issues | Run health check, address warnings |

---

**Next Steps**:
- Set up Grafana for advanced monitoring (optional)
- Create custom alert rules in `configs/alerting_rules.yaml`
- Integrate with PagerDuty for production (when ready)
