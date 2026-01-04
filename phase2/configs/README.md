# Configuration Files

This directory contains configuration files for various system components.

## Monitoring Configuration

### prometheus.yml
Prometheus configuration for scraping metrics from the pipeline monitoring service.

**Key Settings:**
- Scrape interval: 15 seconds
- Evaluation interval: 15 seconds
- Retention: 90 days
- Scrape targets: pipeline-monitor, backend-api

**Customization:**
- Adjust scrape intervals for performance tuning
- Add additional scrape targets for new services
- Configure external labels for multi-cluster setups

### prometheus-alerts.yml
Alert rules for Prometheus to detect critical conditions.

**Configured Alerts:**
- Pipeline execution failures
- Low success rate
- Stale data/forecasts
- Slow execution
- Service downtime

**Customization:**
- Adjust thresholds (e.g., staleness from 7 to 14 days)
- Modify alert duration (e.g., `for: 5m` to `for: 10m`)
- Add custom alert rules for specific conditions

### grafana-dashboard.json
Pre-configured Grafana dashboard for pipeline monitoring.

**Panels:**
- Execution status and metrics
- Data and forecast freshness
- Success/failure rates
- Duration trends
- Records processed

**Customization:**
1. Import dashboard in Grafana UI
2. Edit panels and queries
3. Export updated JSON
4. Replace this file with exported JSON

### grafana-datasources.yml
Grafana datasource configuration for Prometheus.

**Settings:**
- Datasource: Prometheus
- URL: http://prometheus:9090
- Default: Yes
- Query timeout: 60s

**Customization:**
- Add additional datasources (e.g., PostgreSQL, InfluxDB)
- Adjust query timeout for slow queries
- Configure authentication if needed

## Pipeline Configuration

### trigger_thresholds.yaml
Insurance trigger thresholds for different regions and crops.

See `modules/calibration/` for threshold calibration tools.

## Usage

### Development
Configuration files are mounted as volumes in Docker containers:
```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d
```

### Production
Ensure all configuration files are properly secured and backed up:
```bash
# Backup configurations
tar czf configs-backup-$(date +%Y%m%d).tar.gz configs/

# Restore configurations
tar xzf configs-backup-20241126.tar.gz
```

### Validation

**Validate Prometheus config:**
```bash
docker run --rm -v $(pwd)/configs:/configs prom/prometheus:latest \
  promtool check config /configs/prometheus.yml
```

**Validate alert rules:**
```bash
docker run --rm -v $(pwd)/configs:/configs prom/prometheus:latest \
  promtool check rules /configs/prometheus-alerts.yml
```

## Security Notes

- Do not commit sensitive credentials to version control
- Use environment variables for secrets
- Restrict file permissions in production (chmod 600)
- Regularly rotate credentials and API keys
- Use encrypted connections (TLS/SSL) in production

## Documentation

For detailed setup and configuration instructions, see:
- `docs/MONITORING_SETUP.md` - Monitoring infrastructure setup
- `docs/DOCKER_DEPLOYMENT.md` - Docker deployment guide
- `backend/DEPLOYMENT_GUIDE.md` - Backend deployment guide
