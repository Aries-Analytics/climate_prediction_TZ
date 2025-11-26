# Design Document

## Overview

The Automated Forecast Pipeline transforms the manual climate data ingestion and forecast generation process into an autonomous, production-ready system. This design leverages existing ingestion modules, forecast services, and database infrastructure while adding scheduling, monitoring, alerting, and health check capabilities.

**Key Design Principles:**
- **Reuse Existing Components**: Leverage 90% of existing code (ingestion modules, forecast service, database models)
- **Minimal New Code**: Focus on orchestration, scheduling, and monitoring layers
- **Graceful Degradation**: Continue operation when individual data sources fail
- **Observable**: Comprehensive logging, metrics, and health checks
- **Configurable**: Environment-driven configuration for deployment flexibility

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scheduler Service                         │
│  (APScheduler with persistent job store)                    │
└────────────────┬────────────────────────────────────────────┘
                 │ Triggers daily at 06:00 UTC
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Pipeline Orchestrator                           │
│  - Execution locking (prevent concurrent runs)              │
│  - Stage coordination (ingestion → forecast)                │
│  - Error handling & retry logic                             │
│  - Progress tracking                                         │
└────┬────────────────────────────────────┬───────────────────┘
     │                                    │
     ▼                                    ▼
┌─────────────────────┐      ┌──────────────────────────────┐
│  Data Ingestion     │      │   Forecast Generation        │
│  (Existing Modules) │      │   (Existing Service)         │
│  - CHIRPS           │      │   - Load trained model       │
│  - NASA POWER       │      │   - Generate predictions     │
│  - ERA5             │      │   - Store forecasts          │
│  - NDVI             │      │   - Create recommendations   │
│  - Ocean Indices    │      │                              │
└─────────┬───────────┘      └──────────────┬───────────────┘
          │                                 │
          └────────────┬────────────────────┘
                       ▼
          ┌──────────────────────────────────────────┐
          │         PostgreSQL Database              │
          │  - climate_data (daily records)          │
          │  - forecasts (predictions)               │
          │  - pipeline_executions (audit log)       │
          │  - data_quality_metrics                  │
          └──────────────┬───────────────────────────┘
                         │
          ┌──────────────┴───────────────────────────┐
          │                                          │
          ▼                                          ▼
┌──────────────────────┐              ┌──────────────────────┐
│  Monitoring Service  │              │   Alert Service      │
│  - Health checks     │              │   - Email alerts     │
│  - Metrics export    │              │   - Slack webhooks   │
│  - Prometheus format │              │   - Log alerts       │
│  - Status API        │              │   - Alert templates  │
└──────────────────────┘              └──────────────────────┘
```

### Component Interaction Flow

**Daily Automated Execution:**
1. Scheduler triggers at 06:00 UTC
2. Orchestrator acquires execution lock
3. Orchestrator queries last successful ingestion date per source
4. Ingestion modules fetch incremental data (last date → today)
5. Data validation runs on ingested data
6. Forecast service generates predictions using latest data
7. Recommendations generated for high-risk forecasts
8. Execution metadata recorded in database
9. Metrics exported for monitoring
10. Lock released

**Failure Handling:**
- API failures → Retry with exponential backoff (3 attempts)
- Single source failure → Continue with other sources, send partial failure alert
- Forecast failure → Retry once after 5 minutes
- Complete failure → Send critical alert, log details

## Components and Interfaces

### 1. Pipeline Scheduler

**Technology**: APScheduler (Python scheduling library)
**Responsibility**: Trigger pipeline execution on schedule

**Interface:**
```python
class PipelineScheduler:
    def __init__(self, config: SchedulerConfig):
        """Initialize scheduler with cron expression and job store"""
        
    def start(self) -> None:
        """Start the scheduler (non-blocking)"""
        
    def stop(self) -> None:
        """Gracefully stop the scheduler"""
        
    def trigger_manual_run(self) -> ExecutionResult:
        """Manually trigger pipeline execution"""
        
    def get_next_run_time(self) -> datetime:
        """Get next scheduled execution time"""
```

**Configuration:**
- `PIPELINE_SCHEDULE`: Cron expression (default: "0 6 * * *" for 06:00 UTC daily)
- `PIPELINE_TIMEZONE`: Timezone for scheduling (default: "UTC")
- `PIPELINE_JOB_STORE`: Database URL for persistent job storage

### 2. Pipeline Orchestrator

**Responsibility**: Coordinate pipeline stages, handle locking, manage retries

**Interface:**
```python
class PipelineOrchestrator:
    def execute_pipeline(self, execution_id: str) -> ExecutionResult:
        """Execute full pipeline: ingestion → validation → forecasting"""
        
    def execute_ingestion(self, incremental: bool = True) -> IngestionResult:
        """Execute data ingestion with incremental update logic"""
        
    def execute_forecasting(self) -> ForecastResult:
        """Execute forecast generation and recommendations"""
        
    def get_execution_status(self, execution_id: str) -> ExecutionStatus:
        """Get current status of pipeline execution"""
        
    def acquire_lock(self) -> bool:
        """Acquire execution lock to prevent concurrent runs"""
        
    def release_lock(self) -> None:
        """Release execution lock"""
```

**Key Logic:**
- Execution locking using database advisory locks
- Incremental update: Query `MAX(date)` from `climate_data` per source
- Retry logic with exponential backoff
- Progress tracking via database updates
- Error aggregation and reporting

### 3. Incremental Ingestion Manager

**Responsibility**: Determine what data to fetch based on last successful ingestion

**Interface:**
```python
class IncrementalIngestionManager:
    def get_last_ingestion_date(self, source: str) -> Optional[date]:
        """Query database for most recent data date for a source"""
        
    def calculate_fetch_range(self, source: str) -> DateRange:
        """Calculate start/end dates for incremental fetch"""
        
    def mark_ingestion_complete(self, source: str, end_date: date) -> None:
        """Record successful ingestion completion"""
```

**Logic:**
```python
def calculate_fetch_range(source):
    last_date = get_last_ingestion_date(source)
    if last_date is None:
        # No previous data, fetch default lookback
        start_date = today() - timedelta(days=180)
    else:
        # Incremental: fetch from last date + 1 day
        start_date = last_date + timedelta(days=1)
    
    end_date = today()
    return DateRange(start_date, end_date)
```

### 4. Alert Service

**Responsibility**: Send notifications via configured channels

**Interface:**
```python
class AlertService:
    def send_alert(self, alert: Alert) -> None:
        """Send alert to all configured channels"""
        
    def send_pipeline_failure(self, execution_id: str, error: Exception) -> None:
        """Send critical alert for pipeline failure"""
        
    def send_data_staleness_alert(self, source: str, last_date: date) -> None:
        """Send warning for stale data"""
        
    def send_partial_failure_alert(self, failed_sources: List[str]) -> None:
        """Send warning for partial ingestion failure"""
```

**Alert Channels:**
- **Email**: SMTP configuration for email alerts
- **Slack**: Webhook URL for Slack notifications
- **Logging**: Structured logs for alert aggregation

**Configuration:**
- `ALERT_EMAIL_ENABLED`: Enable/disable email alerts
- `ALERT_EMAIL_RECIPIENTS`: Comma-separated email addresses
- `ALERT_SLACK_ENABLED`: Enable/disable Slack alerts
- `ALERT_SLACK_WEBHOOK_URL`: Slack webhook URL

### 5. Monitoring Service

**Responsibility**: Expose metrics and health checks

**Interface:**
```python
class MonitoringService:
    def get_health_status(self) -> HealthStatus:
        """Return current system health"""
        
    def get_metrics(self) -> Dict[str, float]:
        """Return Prometheus-formatted metrics"""
        
    def record_execution_metrics(self, result: ExecutionResult) -> None:
        """Record pipeline execution metrics"""
```

**Metrics Exposed:**
- `pipeline_execution_duration_seconds`: Histogram of execution times
- `pipeline_execution_total`: Counter of total executions
- `pipeline_execution_failures_total`: Counter of failures
- `pipeline_data_records_ingested_total`: Counter of records ingested
- `pipeline_forecasts_generated_total`: Counter of forecasts generated
- `pipeline_last_success_timestamp`: Gauge of last successful execution
- `data_freshness_days`: Gauge of data age in days

**Health Check Endpoint:**
```
GET /health
Response:
{
  "status": "healthy" | "degraded" | "unhealthy",
  "last_execution": "2024-11-25T06:00:00Z",
  "data_freshness_days": 0,
  "forecast_freshness_days": 0,
  "failed_sources": []
}
```

### 6. Data Quality Validator

**Responsibility**: Validate ingested data quality

**Interface:**
```python
class DataQualityValidator:
    def validate_climate_data(self, df: pd.DataFrame) -> ValidationResult:
        """Validate climate data quality"""
        
    def check_required_fields(self, df: pd.DataFrame) -> List[str]:
        """Check for missing required fields"""
        
    def check_value_ranges(self, df: pd.DataFrame) -> List[Anomaly]:
        """Check for out-of-range values"""
        
    def detect_data_gaps(self, df: pd.DataFrame) -> List[DateRange]:
        """Detect missing date ranges"""
```

**Validation Rules:**
- Temperature: -50°C to 60°C
- Rainfall: 0mm to 1000mm per day
- NDVI: -1.0 to 1.0
- Required fields: date, at least one climate variable
- Date continuity: Flag gaps > 7 days

## Data Models

### Pipeline Execution Model

```python
class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"
    
    id = Column(String, primary_key=True)  # UUID
    execution_type = Column(String)  # 'scheduled' | 'manual'
    status = Column(String)  # 'running' | 'completed' | 'failed'
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Ingestion metrics
    records_fetched = Column(Integer, default=0)
    records_stored = Column(Integer, default=0)
    sources_succeeded = Column(ARRAY(String), default=[])
    sources_failed = Column(ARRAY(String), default=[])
    
    # Forecast metrics
    forecasts_generated = Column(Integer, default=0)
    recommendations_created = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
```

### Data Quality Metrics Model

```python
class DataQualityMetrics(Base):
    __tablename__ = "data_quality_metrics"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String, ForeignKey("pipeline_executions.id"))
    source = Column(String, nullable=False)
    checked_at = Column(DateTime, nullable=False)
    
    # Quality metrics
    total_records = Column(Integer)
    missing_values_count = Column(Integer)
    out_of_range_count = Column(Integer)
    data_gaps_count = Column(Integer)
    quality_score = Column(Numeric(3, 2))  # 0.00 to 1.00
    
    # Anomalies
    anomalies = Column(JSON, nullable=True)  # List of detected anomalies
```

### Source Ingestion Tracking Model

```python
class SourceIngestionTracking(Base):
    __tablename__ = "source_ingestion_tracking"
    
    source = Column(String, primary_key=True)
    last_successful_date = Column(Date, nullable=False)
    last_execution_id = Column(String, ForeignKey("pipeline_executions.id"))
    updated_at = Column(DateTime, nullable=False)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Scheduled execution triggers at configured time
*For any* configured schedule, when the system clock reaches the scheduled time, the pipeline execution should be triggered automatically.
**Validates: Requirements 1.1**

### Property 2: Successful ingestion triggers forecast generation
*For any* successful data ingestion, the forecast generation stage should be automatically triggered.
**Validates: Requirements 1.2**

### Property 3: Concurrent execution prevention
*For any* attempt to start a pipeline execution while another is running, the system should prevent the concurrent execution and return an error.
**Validates: Requirements 1.3, 7.2**

### Property 4: Execution metadata persistence
*For any* pipeline execution (successful or failed), the system should record execution metadata (timestamp, status, duration) in the database.
**Validates: Requirements 1.4**

### Property 5: Incremental fetch date calculation
*For any* data source with existing data, the system should query the most recent date and fetch only data from that date forward.
**Validates: Requirements 2.1, 2.2**

### Property 6: Independent source tracking
*For any* set of data sources with different last-update dates, the system should handle each source's incremental update independently.
**Validates: Requirements 2.5**

### Property 7: Alert delivery on failure
*For any* pipeline execution failure, the system should send an alert via configured channels within the specified time limit.
**Validates: Requirements 3.1**

### Property 8: Staleness detection and alerting
*For any* climate data or forecast older than the configured threshold (7 days), the system should send a staleness alert.
**Validates: Requirements 3.2, 3.3**

### Property 9: Partial failure warning
*For any* pipeline execution where at least one data source fails but others succeed, the system should send a partial failure warning.
**Validates: Requirements 3.4**

### Property 10: Alert content completeness
*For any* alert sent, the message should include error details, timestamp, and affected components.
**Validates: Requirements 3.5**

### Property 11: Retry with exponential backoff
*For any* API call failure, the system should retry up to the configured maximum (3 times) with exponentially increasing delays.
**Validates: Requirements 4.1**

### Property 12: Graceful degradation on single source failure
*For any* single data source failure after retries, the system should continue processing other sources successfully.
**Validates: Requirements 4.2**

### Property 13: Forecast retry logic
*For any* forecast generation failure, the system should retry once after the configured delay (5 minutes).
**Validates: Requirements 4.3**

### Property 14: Final failure handling
*For any* scenario where all retries are exhausted, the system should log the failure details and send an alert.
**Validates: Requirements 4.4**

### Property 15: Partial data forecast generation
*For any* scenario with partial data availability, the system should generate forecasts using available data and flag reduced confidence.
**Validates: Requirements 4.5**

### Property 16: Data freshness display
*For any* dashboard view, the system should display the timestamp of the most recent climate data.
**Validates: Requirements 5.1**

### Property 17: Forecast timestamp display
*For any* forecast view, the system should display the forecast generation timestamp.
**Validates: Requirements 5.2**

### Property 18: Staleness warning indicator
*For any* data older than the staleness threshold (7 days), the system should display a warning indicator.
**Validates: Requirements 5.3**

### Property 19: Running status indicator
*For any* currently executing pipeline, the system should display an "updating" status indicator.
**Validates: Requirements 5.4**

### Property 20: Execution logging completeness
*For any* pipeline execution, the system should log start time, end time, and duration.
**Validates: Requirements 6.1**

### Property 21: Per-source logging
*For any* data source processed, the system should log records fetched, processed, and stored.
**Validates: Requirements 6.2**

### Property 22: Error logging with stack traces
*For any* error that occurs, the system should log the full stack trace and context information.
**Validates: Requirements 6.3**

### Property 23: Performance metrics persistence
*For any* pipeline execution completion, the system should record performance metrics in the database.
**Validates: Requirements 6.4**

### Property 24: Log retention and querying
*For any* query for pipeline history, the system should provide access to the last 90 days of execution logs.
**Validates: Requirements 6.5**

### Property 25: Manual trigger execution
*For any* manual trigger invocation, the system should execute the pipeline immediately.
**Validates: Requirements 7.1**

### Property 26: Status reporting accuracy
*For any* status query, the system should return the current execution state (idle, running, failed) accurately.
**Validates: Requirements 7.3**

### Property 27: Progress tracking
*For any* running pipeline, the system should provide progress information for each stage.
**Validates: Requirements 7.4**

### Property 28: Manual execution summary
*For any* completed manual execution, the system should return a summary of results and any errors.
**Validates: Requirements 7.5**

### Property 29: Required field validation
*For any* ingested climate data, the system should validate that required fields are present.
**Validates: Requirements 8.1**

### Property 30: Anomaly detection
*For any* data values outside expected ranges, the system should flag them as anomalies for review.
**Validates: Requirements 8.2**

### Property 31: Data gap detection
*For any* data with missing date ranges, the system should log the gaps.
**Validates: Requirements 8.3**

### Property 32: Quality failure alerting
*For any* data quality check failure, the system should send an alert with details of the issues.
**Validates: Requirements 8.4**

### Property 33: Quality metrics persistence
*For any* validation run, the system should store data quality metrics in the database.
**Validates: Requirements 8.5**

### Property 34: Configuration loading
*For any* system start, the system should load configuration from environment variables and config files.
**Validates: Requirements 9.1**

### Property 35: Schedule configuration
*For any* configured cron expression, the system should use it for scheduling.
**Validates: Requirements 9.2**

### Property 36: Multi-channel alerting
*For any* configured alert channels, the system should send notifications to all enabled channels.
**Validates: Requirements 9.3**

### Property 37: Retry configuration
*For any* configured retry parameters, the system should use the specified retry counts and delays.
**Validates: Requirements 9.4**

### Property 38: Configuration validation
*For any* invalid configuration, the system should fail fast with clear error messages.
**Validates: Requirements 9.5**

### Property 39: Prometheus metrics format
*For any* pipeline execution, the system should expose metrics in Prometheus format.
**Validates: Requirements 10.1**

### Property 40: Health check endpoint
*For any* health check request, the system should provide an HTTP endpoint returning system status.
**Validates: Requirements 10.2**

### Property 41: Health status updates on failure
*For any* pipeline failure, the system should update the health check status to unhealthy.
**Validates: Requirements 10.3**

### Property 42: Metrics completeness
*For any* metrics collection, the system should include execution duration, success rate, and data volume.
**Validates: Requirements 10.4**

## Error Handling

### Error Categories and Responses

**1. Transient Errors (Retry)**
- Network timeouts
- API rate limits
- Temporary service unavailability

**Response**: Exponential backoff retry (3 attempts)

**2. Data Source Errors (Graceful Degradation)**
- Single source API failure after retries
- Data format issues from one source

**Response**: Continue with other sources, send partial failure alert

**3. System Errors (Critical Alert)**
- Database connection failure
- Model loading failure
- Configuration errors

**Response**: Fail fast, send critical alert, log details

**4. Data Quality Errors (Warning)**
- Out-of-range values
- Missing fields
- Data gaps

**Response**: Flag for review, continue processing, send quality alert

### Retry Configuration

```python
RETRY_CONFIG = {
    'max_attempts': 3,
    'initial_delay': 2,  # seconds
    'backoff_factor': 2,  # exponential: 2s, 4s, 8s
    'max_delay': 60,  # cap at 60 seconds
}
```

### Error Logging Format

```python
{
    "timestamp": "2024-11-25T06:15:23Z",
    "execution_id": "uuid-here",
    "error_type": "DataSourceError",
    "error_message": "CHIRPS API timeout",
    "source": "chirps_ingestion",
    "stack_trace": "...",
    "context": {
        "date_range": "2024-11-18 to 2024-11-25",
        "retry_attempt": 3
    }
}
```

## Testing Strategy

### Unit Testing

**Focus Areas:**
- Configuration loading and validation
- Date range calculation for incremental updates
- Retry logic with exponential backoff
- Alert message formatting
- Data quality validation rules
- Execution lock acquisition/release

**Example Tests:**
```python
def test_incremental_date_calculation():
    """Test that incremental fetch calculates correct date range"""
    # Given: Last ingestion date is 2024-11-20
    # When: Calculating fetch range on 2024-11-25
    # Then: Should fetch 2024-11-21 to 2024-11-25

def test_retry_exponential_backoff():
    """Test retry delays follow exponential backoff"""
    # Given: Retry config with factor 2
    # When: Retrying 3 times
    # Then: Delays should be 2s, 4s, 8s

def test_concurrent_execution_prevention():
    """Test that concurrent executions are prevented"""
    # Given: Pipeline is running
    # When: Attempting to start another execution
    # Then: Should raise ConcurrentExecutionError
```

### Property-Based Testing

**Testing Framework**: Hypothesis (Python)

**Property Tests:**
- Incremental date calculation for any last-update date
- Retry logic for any number of failures
- Alert delivery for any error type
- Configuration validation for any config values
- Data quality validation for any input data

### Integration Testing

**Focus Areas:**
- End-to-end pipeline execution
- Database interactions (locking, metrics storage)
- Alert delivery to actual channels (with test webhooks)
- Scheduler triggering
- Health check endpoint responses

**Test Environment:**
- Test database with sample data
- Mock external APIs (CHIRPS, NASA POWER, etc.)
- Test Slack webhook
- Test email SMTP server

### Performance Testing

**Metrics to Validate:**
- Pipeline execution completes within 5 minutes (Requirement 4.4 from Early Warning System)
- Incremental ingestion is faster than full re-fetch
- Database queries for last-update dates complete in <1 second
- Health check endpoint responds in <100ms

## Deployment Considerations

### Environment Variables

```bash
# Scheduling
PIPELINE_SCHEDULE="0 6 * * *"  # Daily at 06:00 UTC
PIPELINE_TIMEZONE="UTC"
PIPELINE_ENABLE_SCHEDULER=true

# Database
DATABASE_URL="postgresql://user:pass@host:5432/db"

# Alerting
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST="smtp.gmail.com"
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM="alerts@example.com"
ALERT_EMAIL_RECIPIENTS="admin@example.com,ops@example.com"

ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=2
RETRY_BACKOFF_FACTOR=2

# Data Quality
DATA_STALENESS_THRESHOLD_DAYS=7
FORECAST_STALENESS_THRESHOLD_DAYS=7

# Monitoring
MONITORING_PORT=9090
HEALTH_CHECK_PORT=8080
```

### Docker Deployment

```dockerfile
# Dockerfile for pipeline service
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run scheduler service
CMD ["python", "-m", "backend.services.pipeline_scheduler"]
```

### Docker Compose Integration

```yaml
services:
  pipeline-scheduler:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - PIPELINE_SCHEDULE=${PIPELINE_SCHEDULE}
      - ALERT_SLACK_WEBHOOK_URL=${ALERT_SLACK_WEBHOOK_URL}
    depends_on:
      - db
    restart: unless-stopped
    
  pipeline-monitor:
    build: .
    command: python -m backend.services.monitoring_service
    ports:
      - "9090:9090"  # Metrics
      - "8080:8080"  # Health checks
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
    restart: unless-stopped
```

### Monitoring Integration

**Prometheus Scrape Configuration:**
```yaml
scrape_configs:
  - job_name: 'climate-pipeline'
    static_configs:
      - targets: ['pipeline-monitor:9090']
    scrape_interval: 30s
```

**Grafana Dashboard Panels:**
- Pipeline execution success rate (last 24h, 7d, 30d)
- Average execution duration
- Data freshness gauge
- Forecast freshness gauge
- Failed sources count
- Alert frequency

### Production Checklist

- [ ] Database migrations applied (new tables for pipeline_executions, etc.)
- [ ] Environment variables configured
- [ ] Alert channels tested (send test alert)
- [ ] Scheduler service deployed and running
- [ ] Monitoring service deployed and accessible
- [ ] Health check endpoint responding
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboard configured
- [ ] Manual trigger tested
- [ ] Logs aggregated to central logging system
- [ ] Backup strategy for pipeline execution history

## Security Considerations

### Secrets Management
- Store API keys, database passwords, SMTP credentials in environment variables
- Use secrets management service (AWS Secrets Manager, HashiCorp Vault) in production
- Never commit secrets to version control

### API Rate Limiting
- Respect external API rate limits (CHIRPS, NASA POWER)
- Implement client-side rate limiting if needed
- Use exponential backoff to avoid overwhelming APIs

### Database Security
- Use advisory locks for execution locking (prevents SQL injection)
- Parameterized queries for all database operations
- Least-privilege database user for pipeline service

### Alert Security
- Sanitize error messages in alerts (remove sensitive data)
- Use HTTPS for Slack webhooks
- Use TLS for SMTP connections

## Future Enhancements

### Phase 2 Enhancements (Post-MVP)
1. **Multi-region Support**: Run pipeline for multiple geographic regions
2. **Dynamic Scheduling**: Adjust schedule based on data source update frequencies
3. **Advanced Anomaly Detection**: ML-based anomaly detection for data quality
4. **Pipeline Visualization**: Real-time dashboard showing pipeline progress
5. **A/B Testing**: Compare forecast accuracy with different data freshness
6. **Cost Optimization**: Track API costs and optimize fetch strategies
7. **Webhook Notifications**: Allow external systems to subscribe to pipeline events
8. **Pipeline Replay**: Re-run pipeline for historical dates for testing

### Scalability Considerations
- Current design handles single-region, daily execution
- For higher frequency (hourly), consider:
  - Distributed task queue (Celery, RQ)
  - Horizontal scaling of workers
  - Caching layer for frequently accessed data
- For multiple regions:
  - Partition database by region
  - Parallel execution per region
  - Region-specific alert channels
