# Monitoring and Alerting Setup Guide

This guide covers setting up comprehensive monitoring and alerting infrastructure for the Climate Early Warning System automated pipeline.

## Overview

The monitoring infrastructure consists of:

1. **Pipeline Monitor Service**: Exposes metrics and health checks
2. **Prometheus**: Collects and stores time-series metrics
3. **Grafana**: Visualizes metrics with dashboards
4. **Alert Service**: Sends notifications via email and Slack
5. **Alert Rules**: Automated alerts for critical conditions

## Architecture

```
┌─────────────────┐
│ Pipeline        │
│ Scheduler       │──┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌─────────────────┐
│ Pipeline        │  │    │ Prometheus      │
│ Monitor         │◄─┼───►│ (Metrics Store) │
│ (Port 9090)     │  │    └────────┬────────┘
└─────────────────┘  │             │
                     │             │
┌─────────────────┐  │    ┌────────▼────────┐
│ Backend API     │──┘    │ Grafana         │
└─────────────────┘       │ (Visualization) │
                          └─────────────────┘
                                   │
                          ┌────────▼────────┐
                          │ Alert Service   │
                          │ (Email/Slack)   │
                          └─────────────────┘
```

## Quick Start

### 1. Start Monitoring Infrastructure

```bash
# Start main services
docker-compose -f docker-compose.dev.yml up -d

# Start monitoring services (Prometheus + Grafana)
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services are running
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Monitoring Interfaces

- **Pipeline Metrics**: http://localhost:9090/metrics
- **Pipeline Health**: http://localhost:8080/health
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3001 (default: admin/admin)

### 3. Configure Alerts

Edit `.env` file with alert configuration:

```bash
# Email Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@yourdomain.com,ops@yourdomain.com
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password

# Slack Alerts
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 4. Test Alert Delivery

```bash
# Test all alert channels
docker-compose -f docker-compose.dev.yml exec backend python scripts/test_alerts.py

# Or test from host
cd backend
python scripts/test_alerts.py
```

## Detailed Setup

### Prometheus Configuration

Prometheus is configured via `configs/prometheus.yml`:

**Key Settings:**
- **Scrape Interval**: 15 seconds (how often to collect metrics)
- **Evaluation Interval**: 15 seconds (how often to evaluate alert rules)
- **Retention**: 90 days (how long to keep metrics)

**Scrape Targets:**
- `pipeline-monitor:9090` - Pipeline monitoring service
- `backend:8000` - Backend API (if exposing metrics)

**Alert Rules:**
Alert rules are defined in `configs/prometheus-alerts.yml`:
- Pipeline execution failures
- Low success rate
- Stale data/forecasts
- Slow execution
- Service downtime

### Grafana Dashboard

Grafana provides visual dashboards for monitoring.

**Initial Setup:**

1. Access Grafana at http://localhost:3001
2. Login with default credentials (admin/admin)
3. Change password when prompted
4. Dashboard is auto-provisioned from `configs/grafana-dashboard.json`

**Dashboard Panels:**

1. **Pipeline Execution Status**: Success rate with color-coded thresholds
2. **Total Executions**: Cumulative execution count
3. **Failed Executions**: Total failure count
4. **Last Execution Duration**: Most recent execution time
5. **Execution Duration Over Time**: Historical duration trends
6. **Success Rate Over Time**: Historical success rate
7. **Data Freshness**: Age of climate data in days
8. **Forecast Freshness**: Age of forecasts in days
9. **Records Ingested**: Total records processed
10. **Forecasts Generated**: Total forecasts created
11. **Execution Rate**: Executions per hour
12. **Failure Rate**: Failures per hour

**Customizing Dashboards:**

1. Click dashboard title → Edit
2. Modify panels, queries, or thresholds
3. Save changes
4. Export JSON to `configs/grafana-dashboard.json` for persistence

### Email Alert Configuration

**Gmail Setup:**

1. Enable 2-factor authentication on your Google account
2. Generate an app password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the generated password

3. Configure in `.env`:
```bash
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

**Other SMTP Providers:**

**SendGrid:**
```bash
ALERT_EMAIL_SMTP_HOST=smtp.sendgrid.net
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=apikey
ALERT_EMAIL_PASSWORD=your-sendgrid-api-key
```

**AWS SES:**
```bash
ALERT_EMAIL_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your-ses-smtp-username
ALERT_EMAIL_PASSWORD=your-ses-smtp-password
```

**Mailgun:**
```bash
ALERT_EMAIL_SMTP_HOST=smtp.mailgun.org
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=postmaster@your-domain.mailgun.org
ALERT_EMAIL_PASSWORD=your-mailgun-password
```

### Slack Alert Configuration

**Setup Slack Webhook:**

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Climate EWS Alerts")
4. Select your workspace
5. Navigate to "Incoming Webhooks"
6. Activate Incoming Webhooks
7. Click "Add New Webhook to Workspace"
8. Select the channel for alerts
9. Copy the webhook URL

**Configure in `.env`:**
```bash
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

**Slack Message Format:**

Alerts include:
- Color-coded severity (red=critical, yellow=warning, blue=info)
- Alert title and description
- Timestamp
- Affected components
- Error details (for failures)

### Alert Types

The system sends alerts for the following conditions:

#### 1. Pipeline Failure Alert
**Trigger**: Pipeline execution fails
**Contains**:
- Execution ID
- Error message
- Failed data sources
- Execution duration
- Timestamp

#### 2. Staleness Alert
**Trigger**: Data or forecasts exceed age threshold (7 days)
**Contains**:
- Data age in days
- Forecast age in days
- Last update timestamp
- Recommended action

#### 3. Data Quality Alert
**Trigger**: Data quality checks fail
**Contains**:
- Failed validation rules
- Affected data sources
- Quality metrics
- Sample of problematic data

#### 4. Source Failure Alert
**Trigger**: Individual data source fails during ingestion
**Contains**:
- Source name
- Error message
- Retry attempts
- Impact on forecasts

#### 5. System Health Alert
**Trigger**: Service health check fails
**Contains**:
- Service name
- Health status
- Last successful check
- Diagnostic information

## Available Metrics

### Pipeline Execution Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `pipeline_execution_total` | Counter | Total number of pipeline executions |
| `pipeline_execution_failures_total` | Counter | Total number of failed executions |
| `pipeline_execution_success_rate` | Gauge | Success rate (0-1) |
| `pipeline_execution_duration_seconds` | Gauge | Duration of last execution |
| `pipeline_last_success_timestamp` | Gauge | Unix timestamp of last successful execution |

### Data Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `pipeline_data_records_ingested_total` | Counter | Total records ingested |
| `pipeline_forecasts_generated_total` | Counter | Total forecasts generated |
| `data_freshness_days` | Gauge | Age of most recent data in days |
| `forecast_freshness_days` | Gauge | Age of most recent forecast in days |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `up` | Gauge | Service availability (1=up, 0=down) |

## Querying Metrics

### Prometheus Query Examples

**Success rate over last hour:**
```promql
rate(pipeline_execution_total[1h]) - rate(pipeline_execution_failures_total[1h])
```

**Average execution duration (5m window):**
```promql
avg_over_time(pipeline_execution_duration_seconds[5m])
```

**Failure rate per hour:**
```promql
rate(pipeline_execution_failures_total[1h]) * 3600
```

**Data staleness alert:**
```promql
data_freshness_days > 7
```

**Forecast generation rate:**
```promql
rate(pipeline_forecasts_generated_total[1h])
```

### Using Grafana Query Builder

1. Open dashboard panel editor
2. Select "Prometheus" as data source
3. Enter PromQL query
4. Adjust time range and refresh interval
5. Configure visualization type (graph, stat, gauge, etc.)

## Alert Rule Configuration

Alert rules are defined in `configs/prometheus-alerts.yml`.

### Adding Custom Alert Rules

1. Edit `configs/prometheus-alerts.yml`
2. Add new rule under appropriate group:

```yaml
- alert: CustomAlertName
  expr: metric_name > threshold
  for: 5m
  labels:
    severity: warning
    component: pipeline
  annotations:
    summary: "Brief description"
    description: "Detailed description with {{ $value }}"
```

3. Reload Prometheus configuration:
```bash
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### Alert Severity Levels

- **critical**: Immediate action required (service down, data loss)
- **warning**: Attention needed (degraded performance, approaching limits)
- **info**: Informational (successful operations, status changes)

## Health Check Endpoints

### Pipeline Monitor Health Check

**Endpoint**: `GET http://localhost:8080/health`

**Response:**
```json
{
  "status": "healthy",
  "last_execution": "2024-11-26T10:30:00Z",
  "data_freshness_days": 1,
  "forecast_freshness_days": 0,
  "failed_sources": []
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Some issues but functional
- `unhealthy`: Critical issues requiring attention

### Backend API Health Check

**Endpoint**: `GET http://localhost:8000/health`

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2024-11-26T10:30:00Z"
}
```

## Troubleshooting

### Prometheus Not Scraping Metrics

**Check target status:**
1. Open Prometheus UI: http://localhost:9091
2. Navigate to Status → Targets
3. Verify targets are "UP"

**Common issues:**
- Service not running: `docker-compose ps`
- Network connectivity: Check Docker networks
- Firewall blocking: Verify port accessibility
- Wrong endpoint: Check `prometheus.yml` configuration

### Grafana Dashboard Not Loading

**Check Prometheus connection:**
1. Open Grafana: http://localhost:3001
2. Navigate to Configuration → Data Sources
3. Click "Prometheus"
4. Click "Test" button

**Common issues:**
- Prometheus URL incorrect: Should be `http://prometheus:9090`
- Prometheus not running: Check with `docker-compose ps`
- Dashboard not provisioned: Check `configs/grafana-dashboard.json`

### Email Alerts Not Sending

**Test SMTP connection:**
```bash
docker-compose -f docker-compose.dev.yml exec backend python scripts/test_alerts.py
```

**Common issues:**
- Wrong SMTP credentials: Verify username/password
- Port blocked: Try port 465 (SSL) instead of 587 (TLS)
- App password required: Use app-specific password for Gmail
- Firewall blocking: Check outbound SMTP connections

### Slack Alerts Not Sending

**Test webhook:**
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```

**Common issues:**
- Invalid webhook URL: Regenerate webhook in Slack
- Webhook revoked: Check Slack app settings
- Channel deleted: Recreate webhook for valid channel
- Network issues: Check outbound HTTPS connectivity

### Metrics Not Updating

**Check pipeline monitor logs:**
```bash
docker-compose -f docker-compose.dev.yml logs -f pipeline-monitor
```

**Common issues:**
- Database connection failed: Check DATABASE_URL
- Service crashed: Restart with `docker-compose restart pipeline-monitor`
- Metrics endpoint error: Check `/metrics` endpoint directly

## Performance Tuning

### Prometheus Storage

**Adjust retention period:**
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=30d'  # Reduce from 90d
```

**Reduce scrape frequency:**
```yaml
# In configs/prometheus.yml
global:
  scrape_interval: 30s  # Increase from 15s
```

### Grafana Performance

**Reduce dashboard refresh rate:**
1. Open dashboard settings
2. Change "Refresh" from 30s to 1m or 5m

**Limit query time range:**
1. Set default time range to "Last 24 hours"
2. Avoid querying full 90-day retention

### Alert Throttling

**Prevent alert spam:**
```yaml
# In configs/prometheus-alerts.yml
- alert: PipelineExecutionFailed
  expr: increase(pipeline_execution_failures_total[1h]) > 0
  for: 15m  # Increase from 5m to wait longer before alerting
```

## Production Recommendations

### Security

1. **Change default passwords:**
   - Grafana admin password
   - Prometheus (if exposing externally)

2. **Use HTTPS:**
   - Configure SSL/TLS for Grafana
   - Use reverse proxy (Nginx) for external access

3. **Restrict access:**
   - Don't expose Prometheus/Grafana ports publicly
   - Use VPN or SSH tunneling for remote access
   - Implement authentication for all endpoints

### High Availability

1. **Prometheus:**
   - Use remote storage (e.g., Thanos, Cortex)
   - Configure multiple Prometheus instances
   - Set up federation for multi-cluster monitoring

2. **Grafana:**
   - Use external database (PostgreSQL/MySQL)
   - Configure multiple Grafana instances behind load balancer
   - Enable session persistence

3. **Alerting:**
   - Configure multiple alert channels
   - Use Alertmanager for advanced routing
   - Set up on-call rotations

### Backup and Recovery

**Backup Prometheus data:**
```bash
docker-compose -f docker-compose.monitoring.yml exec prometheus \
  tar czf /prometheus/backup.tar.gz /prometheus/data
```

**Backup Grafana dashboards:**
```bash
# Export all dashboards via API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3001/api/search?type=dash-db | \
  jq -r '.[] | .uid' | \
  xargs -I {} curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3001/api/dashboards/uid/{} > dashboards_backup.json
```

## Integration with External Systems

### PagerDuty Integration

1. Create PagerDuty service
2. Get integration key
3. Configure Alertmanager:

```yaml
# configs/alertmanager.yml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_INTEGRATION_KEY'
```

### Datadog Integration

Use Datadog agent to forward metrics:

```yaml
# docker-compose.monitoring.yml
datadog:
  image: datadog/agent:latest
  environment:
    - DD_API_KEY=YOUR_API_KEY
    - DD_SITE=datadoghq.com
    - DD_PROMETHEUS_SCRAPE_ENABLED=true
```

### AWS CloudWatch Integration

Use CloudWatch exporter:

```yaml
# docker-compose.monitoring.yml
cloudwatch-exporter:
  image: prom/cloudwatch-exporter
  volumes:
    - ./configs/cloudwatch.yml:/config/cloudwatch.yml
```

## Monitoring Checklist

- [ ] Prometheus scraping metrics successfully
- [ ] Grafana dashboard displaying data
- [ ] Email alerts configured and tested
- [ ] Slack alerts configured and tested
- [ ] Alert rules configured for critical conditions
- [ ] Health check endpoints responding
- [ ] Metrics retention configured appropriately
- [ ] Backup strategy implemented
- [ ] Access controls configured
- [ ] Documentation updated with custom configurations

## Support and Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **PromQL Tutorial**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Alert Rule Examples**: https://awesome-prometheus-alerts.grep.to/

For issues specific to the Climate EWS monitoring setup, refer to the main project documentation or contact the development team.
