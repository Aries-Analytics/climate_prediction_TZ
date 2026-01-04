# Automated Forecast Pipeline - Complete Guide

**Version**: 1.0  
**Last Updated**: November 27, 2024  
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Monitoring](#monitoring)
6. [Operations](#operations)
7. [Troubleshooting](#troubleshooting)
8. [Testing](#testing)
9. [API Reference](#api-reference)

---

## Overview

The Automated Forecast Pipeline is a production-ready system that automatically ingests climate data, generates forecasts, and provides early warnings for agricultural risks in Tanzania.

### Key Features

- **Automated Scheduling**: Daily execution at 06:00 UTC (configurable)
- **Incremental Updates**: Fetches only new data since last run
- **Graceful Degradation**: Continues with partial data if sources fail
- **Multi-Channel Alerts**: Email and Slack notifications
- **Health Monitoring**: Prometheus metrics and health checks
- **Concurrent Protection**: Prevents overlapping executions
- **Retry Logic**: Exponential backoff for transient failures

### Data Sources

1. **CHIRPS**: Rainfall data
2. **NASA POWER**: Temperature and solar radiation
3. **ERA5**: Comprehensive climate variables
4. **NDVI**: Vegetation health indices
5. **Ocean Indices**: ENSO, IOD indicators

### Pipeline Stages

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Ingestion  │ ──> │  Validation  │ ──> │ Forecasting │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
  [Database]           [Metrics]            [Alerts]
```

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DATA SOURCES                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ CHIRPS   │  │   NASA   │  │   ERA5   │  │   NDVI   │  │ Ocean Indices    │ │
│  │   API    │  │  POWER   │  │   API    │  │   API    │  │      API         │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼─────────────┼──────────────────┼───────────┘
        │             │             │             │                  │
        └─────────────┴─────────────┴─────────────┴──────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────────────────┐
        │              INCREMENTAL INGESTION MANAGER                     │
        │  • Tracks last ingestion date per source                      │
        │  • Calculates incremental fetch ranges                        │
        │  • Default 180-day lookback for new sources                   │
        └───────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────────────────┐
        │                 PIPELINE ORCHESTRATOR                          │
        │  • Coordinates ingestion → validation → forecasting           │
        │  • Manages execution locking (prevents concurrent runs)       │
        │  • Handles errors with retry logic                            │
        │  • Records execution metadata                                 │
        └─┬─────────────┬─────────────┬─────────────┬───────────────────┘
          │             │             │             │
          ▼             ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │  Retry  │  │  Alert   │  │Monitor   │  │  Scheduler   │
    │ Handler │  │ Service  │  │ Service  │  │ (APScheduler)│
    │         │  │          │  │          │  │              │
    │ • Max 3 │  │ • Email  │  │ • Metrics│  │ • Cron: 0 6  │
    │ attempts│  │ • Slack  │  │ • Health │  │   * * *      │
    │ • Exp.  │  │ • Logs   │  │ • Status │  │ • Manual     │
    │ backoff │  │          │  │          │  │   trigger    │
    └────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘
         │            │             │                │
         └────────────┴─────────────┴────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────────────────┐
        │                    POSTGRESQL DATABASE                         │
        │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
        │  │ Climate Data │  │  Forecasts   │  │ Pipeline Executions│  │
        │  │              │  │              │  │                    │  │
        │  │ • Date       │  │ • Trigger    │  │ • Status           │  │
        │  │ • Location   │  │ • Probability│  │ • Duration         │  │
        │  │ • Variables  │  │ • Horizon    │  │ • Sources          │  │
        │  └──────────────┘  └──────────────┘  └────────────────────┘  │
        └───────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────────────────┐
        │                   MONITORING STACK                             │
        │  ┌──────────────────┐         ┌──────────────────┐            │
        │  │   Prometheus     │  ────>  │     Grafana      │            │
        │  │                  │         │                  │            │
        │  │ • Metrics Store  │         │ • Dashboards     │            │
        │  │ • Alert Rules    │         │ • Visualization  │            │
        │  │ • Port: 9091     │         │ • Port: 3001     │            │
        │  └──────────────────┘         └──────────────────┘            │
        └───────────────────────────────────────────────────────────────┘
```

**Diagram File**: See `docs/diagrams/architecture.md` for interactive Mermaid version

### Component Interaction Diagram (Execution Flow)

```
Scheduler    Orchestrator    Ingestion Mgr    Data Sources    Database    Forecast Svc
    │              │                │                │            │              │
    │ Trigger      │                │                │            │              │
    │ (06:00 UTC)  │                │                │            │              │
    ├─────────────>│                │                │            │              │
    │              │ Acquire Lock   │                │            │              │
    │              ├───────────────>│                │            │              │
    │              │                │                │            │              │
    │              │ Get Last Dates │                │            │              │
    │              ├───────────────>│                │            │              │
    │              │                │ Query Tracking │            │              │
    │              │                ├───────────────────────────>│              │
    │              │                │<───────────────────────────┤              │
    │              │<───────────────┤ Return Dates   │            │              │
    │              │                │                │            │              │
    │              │ ╔═══════════════════════════════════════════╗              │
    │              │ ║  FOR EACH SOURCE (CHIRPS, NASA, etc.)    ║              │
    │              │ ╚═══════════════════════════════════════════╝              │
    │              │                │                │            │              │
    │              │ Fetch Data (incremental range)  │            │              │
    │              ├────────────────────────────────>│            │              │
    │              │<────────────────────────────────┤            │              │
    │              │                │                │            │              │
    │              │ Store Data     │                │            │              │
    │              ├───────────────────────────────────────────>│              │
    │              │                │                │            │              │
    │              │ Update Tracking│                │            │              │
    │              ├───────────────>│                │            │              │
    │              │                ├───────────────────────────>│              │
    │              │                │                │            │              │
    │              │ ╔═══════════════════════════════════════════╗              │
    │              │ ║  END LOOP                                 ║              │
    │              │ ╚═══════════════════════════════════════════╝              │
    │              │                │                │            │              │
    │              │ Generate Forecasts              │            │              │
    │              ├────────────────────────────────────────────────────────────>│
    │              │                │                │            │              │
    │              │                │                │ Query Data │              │
    │              │                │                │<───────────┤              │
    │              │                │                │ Return Data│              │
    │              │                │                ├───────────>│              │
    │              │                │                │            │              │
    │              │                │                │ Store Forecasts           │
    │              │                │                ├───────────>│              │
    │              │<────────────────────────────────────────────────────────────┤
    │              │                │                │            │              │
    │              │ Record Execution Metadata       │            │              │
    │              ├───────────────────────────────────────────>│              │
    │              │                │                │            │              │
    │              │ Record Metrics │                │            │              │
    │              ├───────────────>│                │            │              │
    │              │                │                │            │              │
    │              │ Release Lock   │                │            │              │
    │              ├───────────────>│                │            │              │
    │<─────────────┤                │                │            │              │
    │ Return Result│                │                │            │              │
    │              │                │                │            │              │

IF FAILURE OCCURS:
    │              │                │                │            │              │
    │              │ Send Alert     │                │            │              │
    │              ├───────────────>│                │            │              │
    │              │                │ • Email (SMTP) │            │              │
    │              │                │ • Slack (Webhook)           │              │
    │              │                │                │            │              │
```

**Diagram File**: See `docs/diagrams/sequence.md` for interactive Mermaid version
    
    alt Execution Failed
        O->>A: Send Failure Alert
        A->>A: Send Email
        A->>A: Send Slack
    end
    
    O-->>S: Return Result
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA SOURCES                                      │
│                                                                              │
│  ┌─────────┐  ┌──────────┐  ┌──────┐  ┌──────┐  ┌──────────────┐          │
│  │ CHIRPS  │  │   NASA   │  │ ERA5 │  │ NDVI │  │    Ocean     │          │
│  │Rainfall │  │  POWER   │  │Climate│ │Veg.  │  │   Indices    │          │
│  └────┬────┘  └────┬─────┘  └───┬──┘  └───┬──┘  └──────┬───────┘          │
└───────┼────────────┼────────────┼─────────┼─────────────┼──────────────────┘
        │            │            │         │             │
        └────────────┴────────────┴─────────┴─────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────┐
        │                  INGESTION STAGE                         │
        │                                                          │
        │  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
        │  │ Fetch Data   │───>│ Validate Data│───>│ Transform │ │
        │  │              │    │              │    │   Data    │ │
        │  │ • API calls  │    │ • Schema     │    │ • Normalize│ │
        │  │ • Retry      │    │ • Ranges     │    │ • Enrich  │ │
        │  │ • Incremental│    │ • Quality    │    │ • Format  │ │
        │  └──────────────┘    └──────────────┘    └─────┬─────┘ │
        └────────────────────────────────────────────────┼───────┘
                                                          │
                                                          ▼
        ┌─────────────────────────────────────────────────────────┐
        │                   DATABASE STORAGE                       │
        │                                                          │
        │  ┌──────────────────────────────────────────────────┐   │
        │  │         Climate Data Tables                      │   │
        │  │  • climate_data (time series)                    │   │
        │  │  • source_ingestion_tracking                     │   │
        │  │  • data_quality_metrics                          │   │
        │  └──────────────────────────────────────────────────┘   │
        └────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────────────┐
        │                  PROCESSING STAGE                        │
        │                                                          │
        │  ┌────────────┐    ┌────────────┐    ┌──────────────┐  │
        │  │  Feature   │───>│   Model    │───>│     Post     │  │
        │  │Engineering │    │ Inference  │    │  Processing  │  │
        │  │            │    │            │    │              │  │
        │  │ • Lag vars │    │ • LSTM     │    │ • Threshold  │  │
        │  │ • Rolling  │    │ • Ensemble │    │ • Confidence │  │
        │  │ • Indices  │    │ • Predict  │    │ • Calibrate  │  │
        │  └────────────┘    └────────────┘    └──────┬───────┘  │
        └────────────────────────────────────────────┼────────────┘
                                                      │
                                                      ▼
        ┌─────────────────────────────────────────────────────────┐
        │                      OUTPUTS                             │
        │                                                          │
        │  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
        │  │  Forecasts   │───>│Recommendations│───>│ Triggers  │ │
        │  │              │    │              │    │           │ │
        │  │ • Drought    │    │ • Crop advice│    │ • Payout  │ │
        │  │ • Flood      │    │ • Planting   │    │ • Alert   │ │
        │  │ • Probability│    │ • Irrigation │    │ • Level   │ │
        │  └──────┬───────┘    └──────┬───────┘    └─────┬─────┘ │
        └─────────┼────────────────────┼──────────────────┼───────┘
                  │                    │                  │
                  └────────────────────┴──────────────────┘
                                       │
                                       ▼
                            ┌──────────────────┐
                            │  Alert Service   │
                            │                  │
                            │  • Email         │
                            │  • Slack         │
                            │  • Dashboard     │
                            └──────────────────┘
```

**Diagram Files**: 
- Interactive Mermaid diagrams: `docs/diagrams/`
- Architecture overview: `docs/diagrams/architecture.md`
- Sequence diagrams: `docs/diagrams/sequence.md`
- Data flow: `docs/diagrams/dataflow.md`

---

## Architecture

### System Components

#### 1. Pipeline Orchestrator
**Location**: `backend/app/services/pipeline/orchestrator.py`

Coordinates the entire pipeline execution:
- Manages execution locking
- Coordinates ingestion and forecasting
- Handles errors and retries
- Records execution metadata

#### 2. Incremental Ingestion Manager
**Location**: `backend/app/services/pipeline/incremental_manager.py`

Manages incremental data fetching:
- Tracks last ingestion date per source
- Calculates fetch ranges
- Handles default 180-day lookback
- Updates tracking records

#### 3. Retry Handler
**Location**: `backend/app/services/pipeline/retry_handler.py`

Implements retry logic with exponential backoff:
- Configurable max attempts
- Exponential backoff (2s, 4s, 8s...)
- Max delay cap
- Comprehensive logging

#### 4. Alert Service
**Location**: `backend/app/services/pipeline/alerts.py`

Sends notifications via multiple channels:
- Email alerts (SMTP)
- Slack alerts (webhooks)
- Structured alert templates
- Error handling

#### 5. Monitoring Service
**Location**: `backend/app/services/pipeline/monitoring.py`

Provides metrics and health checks:
- Prometheus-formatted metrics
- Health status endpoint
- Data freshness tracking
- Execution metrics

#### 6. Pipeline Scheduler
**Location**: `backend/app/services/pipeline/scheduler.py`

Manages scheduled and manual executions:
- APScheduler integration
- Cron-based scheduling
- Manual trigger support
- Persistent job store

### Database Models

#### PipelineExecution
Tracks each pipeline run:
```python
- id: Unique execution ID
- execution_type: 'scheduled' | 'manual'
- status: 'running' | 'completed' | 'failed' | 'partial'
- started_at: Start timestamp
- completed_at: End timestamp
- duration_seconds: Execution duration
- records_fetched: Total records fetched
- records_stored: Total records stored
- forecasts_generated: Number of forecasts
- recommendations_created: Number of recommendations
- sources_succeeded: List of successful sources
- sources_failed: List of failed sources
- error_message: Error details (if failed)
```

#### SourceIngestionTracking
Tracks last ingestion per source:
```python
- source: Data source name
- last_successful_date: Last date ingested
- updated_at: Last update timestamp
```

#### DataQualityMetrics
Stores quality metrics:
```python
- execution_id: Related execution
- source: Data source
- records_validated: Number validated
- records_failed: Number failed
- validation_errors: Error details
```

---

## Configuration

### Environment Variables

#### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/climate_prod

# Security
JWT_SECRET=<random-secret-key>

# Pipeline Schedule
PIPELINE_SCHEDULE=0 6 * * *  # Daily at 6 AM UTC
PIPELINE_TIMEZONE=UTC
```

#### Optional Variables

```bash
# Email Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@yourdomain.com,ops@yourdomain.com
ALERT_EMAIL_USERNAME=your_email@gmail.com
ALERT_EMAIL_PASSWORD=your_app_password

# Slack Alerts
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=2
RETRY_BACKOFF_FACTOR=2

# Monitoring
MONITORING_METRICS_PORT=9090
MONITORING_HEALTH_PORT=8080

# Data Quality
DATA_STALENESS_THRESHOLD_DAYS=7
FORECAST_STALENESS_THRESHOLD_DAYS=7
```

### Configuration File

Create `.env` from template:
```bash
cp .env.template .env
# Edit .env with your values
```

---

## Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

### Quick Start

#### Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd climate-early-warning-system

# 2. Configure environment
cp .env.template .env
# Edit .env with your settings

# 3. Start services
docker-compose -f docker-compose.dev.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# 5. Verify services
docker-compose -f docker-compose.dev.yml ps
curl http://localhost:8080/health
```

#### Production Environment

```bash
# 1. Configure production environment
cp .env.template .env
# Set production values (strong passwords, real SMTP, etc.)

# 2. Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. Verify deployment
curl http://localhost:8080/health
curl http://localhost:9090/metrics

# 5. Test manual trigger
docker-compose -f docker-compose.prod.yml exec backend python -m app.cli.pipeline_cli run
```

### Docker Services

#### Pipeline Scheduler
- **Image**: Custom (Dockerfile.scheduler)
- **Purpose**: Runs scheduled pipeline executions
- **Restart**: unless-stopped
- **Health Check**: Python import verification

#### Pipeline Monitor
- **Image**: Custom (Dockerfile.monitoring)
- **Ports**: 9090 (metrics), 8080 (health)
- **Purpose**: Exposes metrics and health checks
- **Restart**: unless-stopped
- **Health Check**: HTTP GET /health

### Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View history
docker-compose exec backend alembic history
```

---

## Monitoring

### Prometheus Metrics

**Endpoint**: `http://localhost:9090/metrics`

#### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `pipeline_execution_total` | Counter | Total executions |
| `pipeline_execution_failures_total` | Counter | Total failures |
| `pipeline_execution_success_rate` | Gauge | Success rate (0-1) |
| `pipeline_execution_duration_seconds` | Gauge | Last execution duration |
| `pipeline_last_success_timestamp` | Gauge | Last successful execution |
| `pipeline_data_records_ingested_total` | Counter | Total records ingested |
| `pipeline_forecasts_generated_total` | Counter | Total forecasts generated |
| `data_freshness_days` | Gauge | Age of data in days |
| `forecast_freshness_days` | Gauge | Age of forecasts in days |

### Health Check

**Endpoint**: `http://localhost:8080/health`

**Response**:
```json
{
  "status": "healthy",
  "last_execution": "2024-11-27T10:30:00Z",
  "data_freshness_days": 0,
  "forecast_freshness_days": 0,
  "failed_sources": []
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some issues but functional
- `unhealthy`: Critical issues

### Grafana Dashboard

1. Access Grafana: `http://localhost:3001`
2. Login: admin/admin (change on first login)
3. Dashboard auto-provisioned from `configs/grafana-dashboard.json`

**Dashboard Panels**:
- Pipeline execution status
- Success/failure rates
- Execution duration trends
- Data and forecast freshness
- Records processed
- Forecasts generated

### Alert Configuration

#### Email Alerts

**Gmail Setup**:
```bash
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=<app-password>  # Generate in Google Account settings
```

#### Slack Alerts

**Webhook Setup**:
1. Go to https://api.slack.com/apps
2. Create new app
3. Enable Incoming Webhooks
4. Add webhook to workspace
5. Copy webhook URL

```bash
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Alert Types

1. **Pipeline Failure**: Complete execution failure
2. **Staleness Alert**: Data/forecasts > 7 days old
3. **Source Failure**: Individual source fails
4. **Data Quality**: Quality checks fail

---

## Operations

### Manual Operations

#### Trigger Manual Run

```bash
# Using Docker
docker-compose exec backend python -m app.cli.pipeline_cli run

# Using CLI directly
cd backend
python -m app.cli.pipeline_cli run --incremental
```

#### Check Pipeline Status

```bash
# Using Docker
docker-compose exec backend python -m app.cli.pipeline_cli status

# View execution history
docker-compose exec backend python -m app.cli.pipeline_cli history --limit 10
```

#### Test Alerts

```bash
# Test all alert channels
docker-compose exec backend python scripts/test_alerts.py

# Test specific channel
docker-compose exec backend python -c "
from app.services.pipeline.alerts import AlertService
import asyncio
asyncio.run(AlertService().send_pipeline_failure_alert(
    'test-123', 'Test alert', [], 60
))
"
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f pipeline-scheduler

# Last 100 lines
docker-compose logs --tail=100 pipeline-monitor

# Since timestamp
docker-compose logs --since 2024-11-27T10:00:00
```

### Database Operations

#### Backup

```bash
# Create backup
docker-compose exec db pg_dump -U user climate_prod > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U user climate_prod > backups/backup_$DATE.sql
find backups/ -mtime +7 -delete  # Keep 7 days
```

#### Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U user climate_prod < backup_20241127.sql
```

#### Query Executions

```sql
-- Recent executions
SELECT id, execution_type, status, started_at, duration_seconds
FROM pipeline_executions
ORDER BY started_at DESC
LIMIT 10;

-- Failed executions
SELECT id, started_at, error_message, sources_failed
FROM pipeline_executions
WHERE status = 'failed'
ORDER BY started_at DESC;

-- Success rate
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN status IN ('completed', 'partial') THEN 1 ELSE 0 END) as successful,
  ROUND(100.0 * SUM(CASE WHEN status IN ('completed', 'partial') THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM pipeline_executions;
```

---

## Troubleshooting

### Common Issues

#### Pipeline Not Running

**Symptoms**: No executions in database, scheduler logs show errors

**Solutions**:
1. Check scheduler is running:
   ```bash
   docker-compose ps pipeline-scheduler
   ```

2. Check scheduler logs:
   ```bash
   docker-compose logs pipeline-scheduler
   ```

3. Verify schedule configuration:
   ```bash
   docker-compose exec pipeline-scheduler env | grep PIPELINE_SCHEDULE
   ```

4. Trigger manual run to test:
   ```bash
   docker-compose exec backend python -m app.cli.pipeline_cli run
   ```

#### Data Not Updating

**Symptoms**: Data freshness > 1 day, no new records

**Solutions**:
1. Check last execution status:
   ```bash
   docker-compose exec backend python -m app.cli.pipeline_cli status
   ```

2. Check for source failures:
   ```sql
   SELECT sources_failed FROM pipeline_executions 
   WHERE started_at > NOW() - INTERVAL '24 hours';
   ```

3. Test individual source:
   ```bash
   docker-compose exec backend python -c "
   from modules.ingestion.chirps_ingestion import ingest_chirps
   ingest_chirps()
   "
   ```

#### Alerts Not Sending

**Symptoms**: Pipeline fails but no alerts received

**Solutions**:
1. Check alert configuration:
   ```bash
   docker-compose exec backend env | grep ALERT_
   ```

2. Test alert delivery:
   ```bash
   docker-compose exec backend python scripts/test_alerts.py
   ```

3. Check alert service logs:
   ```bash
   docker-compose logs backend | grep -i alert
   ```

#### High Memory Usage

**Symptoms**: Container using > 2GB RAM

**Solutions**:
1. Check container stats:
   ```bash
   docker stats
   ```

2. Reduce batch sizes in ingestion
3. Add memory limits:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

#### Database Connection Errors

**Symptoms**: "could not connect to server" errors

**Solutions**:
1. Verify database is running:
   ```bash
   docker-compose ps db
   ```

2. Test connection:
   ```bash
   docker-compose exec db pg_isready -U user
   ```

3. Check connection string:
   ```bash
   docker-compose exec backend env | grep DATABASE_URL
   ```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Pipeline already running" | Concurrent execution attempt | Wait for current execution to complete |
| "Lock acquisition failed" | Database lock issue | Restart services, check database |
| "Source ingestion failed" | External API error | Check API credentials, network |
| "Forecast generation failed" | Model error | Check model files, data quality |
| "SMTP connection failed" | Email config error | Verify SMTP credentials |
| "Webhook request failed" | Slack config error | Verify webhook URL |

---

## Testing

### Test Suite Overview

- **Property Tests**: 41 tests (50+ properties)
- **Integration Tests**: 8 tests
- **Total Coverage**: 79.2% of requirements

### Running Tests

```bash
# All tests
cd backend
python -m pytest tests/ -v

# Property tests only
python -m pytest tests/test_*_properties.py -v

# Integration tests only
python -m pytest tests/test_pipeline_integration.py -v

# Specific test
python -m pytest tests/test_orchestrator_properties.py::test_execution_metadata_persistence -v

# With coverage
python -m pytest tests/ --cov=app.services.pipeline --cov-report=html
```

### Test Categories

#### Property-Based Tests
- Incremental ingestion
- Orchestrator execution
- Retry logic
- Alert delivery
- Scheduler operations
- Monitoring metrics
- Pipeline freshness

#### Integration Tests
- Full pipeline execution
- Incremental updates
- Graceful degradation
- Alert delivery
- Scheduler triggering
- Health checks
- Concurrent execution

---

## API Reference

### CLI Commands

```bash
# Run pipeline
python -m app.cli.pipeline_cli run [--incremental]

# Check status
python -m app.cli.pipeline_cli status

# View history
python -m app.cli.pipeline_cli history [--limit N]

# Test alerts
python -m app.cli.pipeline_cli test-alerts
```

### Python API

```python
from app.services.pipeline.orchestrator import PipelineOrchestrator
from app.services.pipeline.scheduler import PipelineScheduler
from app.core.database import SessionLocal

# Manual execution
db = SessionLocal()
orchestrator = PipelineOrchestrator(db)
result = orchestrator.execute_pipeline(
    execution_type='manual',
    incremental=True
)

# Scheduled execution
scheduler = PipelineScheduler(db)
scheduler.start()  # Start scheduler
result = scheduler.trigger_manual_run()  # Manual trigger
scheduler.stop()  # Stop scheduler
```

### REST API Endpoints

```bash
# Health check
GET /health

# Pipeline status
GET /api/pipeline/status

# Execution history
GET /api/pipeline/executions?limit=10

# Data freshness
GET /api/pipeline/freshness

# Metrics (Prometheus format)
GET /metrics
```

---

## Additional Resources

### Documentation
- **Monitoring Setup**: `docs/MONITORING_SETUP.md`
- **Docker Deployment**: `docs/DOCKER_DEPLOYMENT.md`
- **Test Documentation**: `docs/TEST_IMPLEMENTATION_COMPLETE.md`
- **Configuration Reference**: `configs/README.md`

### Support
- **Issues**: GitHub Issues
- **Slack**: #climate-ews channel
- **Email**: support@yourdomain.com

### Version History
- **v1.0** (2024-11-27): Initial production release
  - Automated scheduling
  - Incremental ingestion
  - Multi-channel alerts
  - Comprehensive monitoring
  - Full test coverage

---

**Last Updated**: November 27, 2024  
**Maintained By**: Climate EWS Team
