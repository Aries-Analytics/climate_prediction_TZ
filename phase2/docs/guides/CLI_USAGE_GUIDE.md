# CLI Usage Guide - Pipeline Management

## Overview

The Climate Early Warning System provides a comprehensive command-line interface (CLI) for managing the automated forecast pipeline. The CLI enables manual operations, status monitoring, execution history review, and alert testing.

## Installation

### Option 1: Direct Python Execution
```bash
cd backend
python cli.py pipeline [command]
```

### Option 2: Install as Package (Recommended)
```bash
cd backend
pip install -e .
climate-cli pipeline [command]
```

### Option 3: Use Alias
```bash
# Add to ~/.bashrc or ~/.zshrc
alias pipeline="python /path/to/backend/cli.py pipeline"

# Then use:
pipeline [command]
```

## Commands

### 1. `pipeline run` - Manual Pipeline Execution

Execute the pipeline manually with custom options.

**Validates: Requirements 7.1**

#### Usage
```bash
pipeline run [OPTIONS]
```

#### Options
- `--incremental` / `--full`: Incremental or full data fetch (default: incremental)
- `--sources TEXT`: Comma-separated list of sources (default: all)

#### Examples

**Run with incremental fetch (default):**
```bash
pipeline run
```

**Run with full data fetch:**
```bash
pipeline run --full
```

**Run specific sources only:**
```bash
pipeline run --sources chirps,era5
```

**Run all sources with full fetch:**
```bash
pipeline run --full
```

#### Output Example
```
============================================================
Manual Pipeline Execution
============================================================
Mode: Incremental

Starting pipeline execution...

============================================================
Execution Results
============================================================
Status: COMPLETED
Execution ID: exec-20241127-123456
Duration: 245.32 seconds

Ingestion:
  Records Fetched: 500
  Records Stored: 500
  Sources Succeeded: chirps, nasa_power, era5, ndvi, ocean_indices

Forecasting:
  Forecasts Generated: 25
  Recommendations Created: 15

✓ Pipeline execution completed successfully!
```

---

### 2. `pipeline status` - View Pipeline Status

View current pipeline status and system health.

**Validates: Requirements 7.3**

#### Usage
```bash
pipeline status [OPTIONS]
```

#### Options
- `--execution-id TEXT`: Show specific execution by ID
- `--verbose`: Show detailed information including metrics

#### Examples

**Show current status:**
```bash
pipeline status
```

**Show detailed status with metrics:**
```bash
pipeline status --verbose
```

**Show specific execution:**
```bash
pipeline status --execution-id exec-20241127-123456
```

#### Output Example
```
============================================================
Pipeline Status
============================================================

System Health: HEALTHY

Last Execution: 2024-11-27 12:34:56

Data Freshness:
  Climate Data: 1 days old
  Forecasts: 0 days old

Recent Executions:
      ID              Type       Started           Duration  Status
---  --------------  ---------  ----------------  ----------  ---------
✓    exec-2024112...  manual     2024-11-27 12:34  245s       completed
✓    exec-2024112...  scheduled  2024-11-27 06:00  230s       completed
⚠    exec-2024112...  scheduled  2024-11-26 06:00  180s       partial
✓    exec-2024112...  scheduled  2024-11-25 06:00  225s       completed
```

---

### 3. `pipeline history` - View Execution History

View pipeline execution history with filtering options.

**Validates: Requirements 6.5**

#### Usage
```bash
pipeline history [OPTIONS]
```

#### Options
- `--limit INTEGER`: Number of executions to show (default: 10)
- `--status-filter TEXT`: Filter by status (completed/failed/partial)
- `--days INTEGER`: Show executions from last N days (default: 7)

#### Examples

**Show last 10 executions:**
```bash
pipeline history
```

**Show last 20 executions:**
```bash
pipeline history --limit 20
```

**Show only failed executions:**
```bash
pipeline history --status-filter failed
```

**Show last 30 days:**
```bash
pipeline history --days 30
```

**Combine filters:**
```bash
pipeline history --limit 50 --status-filter partial --days 14
```

#### Output Example
```
================================================================================
Pipeline Execution History
================================================================================

Showing 10 execution(s) from last 7 days

+----+--------------------+-----------+---------------------+----------+---------+-----------+-----------+
|    | Execution ID       | Type      | Started At          | Duration | Records | Forecasts | Status    |
+====+====================+===========+=====================+==========+=========+===========+===========+
| ✓  | exec-20241127-1... | manual    | 2024-11-27 12:34:56 | 245s     | 500     | 25        | completed |
+----+--------------------+-----------+---------------------+----------+---------+-----------+-----------+
| ✓  | exec-20241127-0... | scheduled | 2024-11-27 06:00:00 | 230s     | 480     | 24        | completed |
+----+--------------------+-----------+---------------------+----------+---------+-----------+-----------+
| ⚠  | exec-20241126-0... | scheduled | 2024-11-26 06:00:00 | 180s     | 350     | 18        | partial   |
+----+--------------------+-----------+---------------------+----------+---------+-----------+-----------+

Statistics:
  Total: 10
  Completed: 8 (80.0%)
  Partial: 2 (20.0%)
  Failed: 0 (0.0%)
  Average Duration: 225.5s
```

---

### 4. `pipeline test-alerts` - Test Alert Delivery

Test alert delivery to configured channels.

**Validates: Requirements 3.1**

#### Usage
```bash
pipeline test-alerts [OPTIONS]
```

#### Options
- `--email` / `--no-email`: Test email alerts (default: enabled)
- `--slack` / `--no-slack`: Test Slack alerts (default: enabled)

#### Examples

**Test all channels:**
```bash
pipeline test-alerts
```

**Test email only:**
```bash
pipeline test-alerts --no-slack
```

**Test Slack only:**
```bash
pipeline test-alerts --no-email
```

#### Output Example
```
============================================================
Alert Delivery Test
============================================================

Testing email alerts...
✓ Email alert sent successfully

Testing Slack alerts...
✓ Slack alert sent successfully

============================================================
Test Summary
============================================================
Email: PASSED
Slack: PASSED

✓ All alert tests passed!
```

---

### 5. `pipeline metrics` - Display Metrics

Display Prometheus-formatted metrics for monitoring.

#### Usage
```bash
pipeline metrics
```

#### Output Example
```
============================================================
Pipeline Metrics
============================================================

# TYPE pipeline_execution_total counter
pipeline_execution_total 145.0
# TYPE pipeline_execution_failures_total counter
pipeline_execution_failures_total 5.0
# TYPE pipeline_execution_success_rate gauge
pipeline_execution_success_rate 0.9655172413793104
pipeline_execution_duration_seconds 245.0
pipeline_last_success_timestamp 1701086096.0
# TYPE pipeline_data_records_ingested_total counter
pipeline_data_records_ingested_total 72500.0
# TYPE pipeline_forecasts_generated_total counter
pipeline_forecasts_generated_total 3625.0
data_freshness_days 1.0
forecast_freshness_days 0.0

============================================================
Total Metrics: 9
```

---

## Common Workflows

### Daily Operations

**Check system health:**
```bash
pipeline status
```

**Run manual update:**
```bash
pipeline run
```

**Review recent activity:**
```bash
pipeline history --limit 5
```

### Troubleshooting

**Check for failures:**
```bash
pipeline history --status-filter failed
```

**View specific failed execution:**
```bash
pipeline status --execution-id exec-20241127-123456
```

**Test alert configuration:**
```bash
pipeline test-alerts
```

**Check detailed status:**
```bash
pipeline status --verbose
```

### Monitoring

**View metrics for Prometheus:**
```bash
pipeline metrics
```

**Check data freshness:**
```bash
pipeline status | grep "Data Freshness"
```

**Monitor execution success rate:**
```bash
pipeline history --days 30
```

## Exit Codes

All commands return appropriate exit codes:

- `0`: Success
- `1`: Error or failure

This allows for scripting and automation:

```bash
#!/bin/bash
if pipeline run; then
    echo "Pipeline execution successful"
else
    echo "Pipeline execution failed"
    exit 1
fi
```

## Environment Variables

The CLI respects the following environment variables:

- `DATABASE_URL`: Database connection string
- `ALERT_EMAIL_ENABLED`: Enable/disable email alerts
- `ALERT_SLACK_ENABLED`: Enable/disable Slack alerts
- `ALERT_EMAIL_SMTP_HOST`: SMTP server for email
- `ALERT_SLACK_WEBHOOK_URL`: Slack webhook URL

## Integration with Cron

Schedule automatic pipeline runs:

```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/backend && python cli.py pipeline run >> /var/log/pipeline.log 2>&1

# Run every 6 hours
0 */6 * * * cd /path/to/backend && python cli.py pipeline run --incremental

# Check status hourly
0 * * * * cd /path/to/backend && python cli.py pipeline status >> /var/log/pipeline-status.log
```

## Docker Usage

Run CLI commands in Docker container:

```bash
# Run pipeline
docker-compose -f docker-compose.dev.yml exec backend python cli.py pipeline run

# Check status
docker-compose -f docker-compose.dev.yml exec backend python cli.py pipeline status

# View history
docker-compose -f docker-compose.dev.yml exec backend python cli.py pipeline history
```

## Troubleshooting

### Command Not Found

**Problem**: `pipeline: command not found`

**Solution**:
```bash
# Use full path
python /path/to/backend/cli.py pipeline [command]

# Or install as package
cd backend && pip install -e .
```

### Database Connection Error

**Problem**: `Error: could not connect to database`

**Solution**:
```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Verify database is running
docker-compose ps db

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in the backend directory
cd backend

# Set PYTHONPATH
export PYTHONPATH=/path/to/backend:$PYTHONPATH

# Or use the CLI from backend directory
python cli.py pipeline [command]
```

### Alert Test Failures

**Problem**: `✗ Email alert failed: SMTP connection refused`

**Solution**:
```bash
# Check SMTP configuration
echo $ALERT_EMAIL_SMTP_HOST
echo $ALERT_EMAIL_SMTP_PORT

# Verify credentials
# Check .env file for correct settings

# Test SMTP connection manually
telnet $ALERT_EMAIL_SMTP_HOST $ALERT_EMAIL_SMTP_PORT
```

## Best Practices

### 1. Regular Status Checks
```bash
# Create a monitoring script
#!/bin/bash
STATUS=$(pipeline status | grep "System Health" | awk '{print $3}')
if [ "$STATUS" != "HEALTHY" ]; then
    echo "Warning: System health is $STATUS"
    pipeline status --verbose
fi
```

### 2. Automated Reporting
```bash
# Daily report script
#!/bin/bash
echo "Daily Pipeline Report - $(date)" > report.txt
pipeline status >> report.txt
pipeline history --days 1 >> report.txt
mail -s "Pipeline Daily Report" admin@example.com < report.txt
```

### 3. Error Notification
```bash
# Run with error notification
pipeline run || {
    echo "Pipeline failed at $(date)" | mail -s "Pipeline Failure" admin@example.com
}
```

### 4. Logging
```bash
# Log all operations
pipeline run 2>&1 | tee -a /var/log/pipeline-$(date +%Y%m%d).log
```

## Support

For issues or questions:
- Check logs: `/var/log/pipeline.log`
- Review documentation: `docs/`
- Check system status: `pipeline status --verbose`
- Test alerts: `pipeline test-alerts`

## See Also

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)
- [Monitoring Setup Guide](MONITORING_SETUP.md)
- [API Documentation](../backend/API_DOCUMENTATION.md)
