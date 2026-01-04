# Docker Deployment Guide

This guide covers deploying the Climate Early Warning System with automated pipeline services using Docker and Docker Compose.

## Architecture Overview

The system consists of the following services:

1. **Database (PostgreSQL)**: Stores climate data, forecasts, and pipeline execution metadata
2. **Backend API**: FastAPI application serving REST endpoints
3. **Frontend**: React-based dashboard interface
4. **Pipeline Scheduler**: Automated data ingestion and forecast generation service
5. **Pipeline Monitor**: Metrics and health check service for monitoring
6. **Nginx** (Production only): Reverse proxy and load balancer

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- At least 4GB RAM available for containers
- 20GB disk space for data and logs

## Quick Start

### Development Environment

1. Clone the repository and navigate to the project root:
```bash
cd climate-early-warning-system
```

2. Copy the environment template:
```bash
cp .env.template .env
```

3. Start all services:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. Verify services are running:
```bash
docker-compose -f docker-compose.dev.yml ps
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Metrics: http://localhost:9090/metrics
   - Health Check: http://localhost:8080/health

### Production Environment

1. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with production values
```

2. Build and start services:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Run database migrations:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

4. Verify deployment:
```bash
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8080/health
```

## Service Configuration

### Database Service

The PostgreSQL database stores all application data.

**Environment Variables:**
- `POSTGRES_DB`: Database name (default: climate_prod)
- `POSTGRES_USER`: Database user (default: user)
- `POSTGRES_PASSWORD`: Database password (required in production)

**Volumes:**
- `postgres_data_prod`: Persistent storage for database files

**Health Check:**
- Command: `pg_isready`
- Interval: 10 seconds
- Timeout: 5 seconds
- Retries: 5

### Backend API Service

FastAPI application serving REST endpoints for the dashboard.

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT token generation
- `ALLOWED_ORIGINS`: CORS allowed origins (JSON array)

**Ports:**
- 8000: API endpoint

**Dependencies:**
- Database must be healthy before starting

**Production Settings:**
- Multi-stage build for optimized image size
- 4 Uvicorn workers for concurrent request handling
- Health check endpoint at `/health`

### Frontend Service

React-based dashboard interface.

**Environment Variables:**
- `VITE_API_BASE_URL`: Backend API URL

**Ports:**
- 3000 (dev) / 80 (prod via Nginx)

**Build:**
- Development: Hot-reload enabled
- Production: Optimized static build served by Nginx

### Pipeline Scheduler Service

Automated service for scheduled data ingestion and forecast generation.

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `PIPELINE_SCHEDULE`: Cron expression for schedule (default: `0 6 * * *` - daily at 6 AM UTC)
- `PIPELINE_TIMEZONE`: Timezone for schedule (default: UTC)
- `ALERT_EMAIL_ENABLED`: Enable email alerts (true/false)
- `ALERT_EMAIL_SMTP_HOST`: SMTP server hostname
- `ALERT_EMAIL_SMTP_PORT`: SMTP server port (default: 587)
- `ALERT_EMAIL_FROM`: Sender email address
- `ALERT_EMAIL_RECIPIENTS`: Comma-separated list of recipient emails
- `ALERT_SLACK_ENABLED`: Enable Slack alerts (true/false)
- `ALERT_SLACK_WEBHOOK_URL`: Slack webhook URL for alerts

**Volumes:**
- `./outputs`: Shared volume for model outputs and forecasts

**Health Check:**
- Verifies Python environment is functional
- Interval: 60 seconds
- Start period: 30 seconds

**Restart Policy:**
- `unless-stopped`: Automatically restarts on failure

### Pipeline Monitor Service

Exposes metrics and health check endpoints for monitoring.

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `MONITORING_METRICS_PORT`: Port for Prometheus metrics (default: 9090)
- `MONITORING_HEALTH_PORT`: Port for health check endpoint (default: 8080)

**Ports:**
- 9090: Prometheus metrics endpoint
- 8080: Health check endpoint

**Health Check:**
- HTTP GET to `/health` endpoint
- Interval: 30 seconds
- Start period: 10 seconds

**Restart Policy:**
- `unless-stopped`: Automatically restarts on failure

### Nginx Service (Production Only)

Reverse proxy and load balancer for production deployment.

**Ports:**
- 80: HTTP
- 443: HTTPS (requires SSL certificates)

**Volumes:**
- `./nginx/nginx.conf`: Nginx configuration
- `./nginx/ssl`: SSL certificates directory

**Configuration:**
- Routes `/api/*` to backend service
- Routes all other requests to frontend
- Load balances across backend replicas

## Environment Variables Reference

### Required Variables (Production)

```bash
# Database
POSTGRES_DB=climate_prod
POSTGRES_USER=climate_user
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql://climate_user:<strong-password>@db:5432/climate_prod

# Security
JWT_SECRET=<random-secret-key>
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Pipeline Schedule
PIPELINE_SCHEDULE=0 6 * * *
PIPELINE_TIMEZONE=UTC

# Email Alerts (Optional)
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@yourdomain.com,ops@yourdomain.com

# Slack Alerts (Optional)
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Monitoring
MONITORING_METRICS_PORT=9090
MONITORING_HEALTH_PORT=8080
```

### Optional Variables

```bash
# Frontend
VITE_API_BASE_URL=http://localhost:8000/api

# Pipeline Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BACKOFF_BASE=2
STALENESS_THRESHOLD_DAYS=7
DATA_QUALITY_CHECK_ENABLED=true
```

## Docker Compose Files

### docker-compose.dev.yml

Development environment with:
- Hot-reload enabled for backend and frontend
- Volume mounts for live code changes
- Simplified configuration
- No Nginx (direct access to services)
- Alerts disabled by default

### docker-compose.prod.yml

Production environment with:
- Optimized builds
- Multiple backend replicas
- Nginx reverse proxy
- Health checks for all services
- Restart policies
- Alert configuration

## Common Operations

### Starting Services

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Stopping Services

```bash
# Development
docker-compose -f docker-compose.dev.yml down

# Production
docker-compose -f docker-compose.prod.yml down
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f pipeline-scheduler

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Restarting a Service

```bash
docker-compose -f docker-compose.prod.yml restart pipeline-scheduler
```

### Rebuilding Services

```bash
# Rebuild all services
docker-compose -f docker-compose.prod.yml up -d --build

# Rebuild specific service
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Executing Commands in Containers

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Access database shell
docker-compose -f docker-compose.prod.yml exec db psql -U user -d climate_prod

# Run Python shell in backend
docker-compose -f docker-compose.prod.yml exec backend python

# Trigger manual pipeline run
docker-compose -f docker-compose.prod.yml exec backend python -m app.services.pipeline.cli run
```

### Scaling Services

```bash
# Scale backend to 4 replicas
docker-compose -f docker-compose.prod.yml up -d --scale backend=4
```

## Database Management

### Running Migrations

```bash
# Apply all pending migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Rollback one migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# View migration history
docker-compose -f docker-compose.prod.yml exec backend alembic history
```

### Backup Database

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U user climate_prod > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U user climate_prod < backup_20231120.sql
```

### Database Connection

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U user -d climate_prod
```

## Monitoring and Health Checks

### Health Check Endpoints

```bash
# Backend API health
curl http://localhost:8000/health

# Pipeline monitor health
curl http://localhost:8080/health

# Check all service health
docker-compose -f docker-compose.prod.yml ps
```

### Prometheus Metrics

Access metrics at: http://localhost:9090/metrics

Available metrics:
- `pipeline_execution_duration_seconds`: Time taken for pipeline execution
- `pipeline_execution_total`: Total number of pipeline executions
- `pipeline_execution_failures_total`: Total number of failed executions
- `pipeline_data_records_processed`: Number of records processed per source
- `pipeline_last_execution_timestamp`: Timestamp of last execution

### Grafana Dashboard (Optional)

If you have Grafana set up, import the dashboard configuration:

```bash
# Add Prometheus data source
# URL: http://pipeline-monitor:9090

# Import dashboard from docs/grafana-dashboard.json
```

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
docker-compose -f docker-compose.prod.yml logs service-name
```

2. Verify environment variables:
```bash
docker-compose -f docker-compose.prod.yml config
```

3. Check service dependencies:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Database Connection Issues

1. Verify database is healthy:
```bash
docker-compose -f docker-compose.prod.yml exec db pg_isready -U user
```

2. Check connection string:
```bash
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

3. Test connection from backend:
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import engine; engine.connect()"
```

### Pipeline Not Running

1. Check scheduler logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f pipeline-scheduler
```

2. Verify schedule configuration:
```bash
docker-compose -f docker-compose.prod.yml exec pipeline-scheduler env | grep PIPELINE_SCHEDULE
```

3. Trigger manual run:
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m app.services.pipeline.cli run
```

### High Memory Usage

1. Check container stats:
```bash
docker stats
```

2. Reduce backend workers:
```yaml
# In docker-compose.prod.yml
command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

3. Limit container memory:
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 1G
```

### Disk Space Issues

1. Check disk usage:
```bash
docker system df
```

2. Clean up unused resources:
```bash
docker system prune -a
```

3. Remove old logs:
```bash
docker-compose -f docker-compose.prod.yml exec backend find /app/logs -mtime +30 -delete
```

## Security Best Practices

1. **Use Strong Passwords**: Generate secure passwords for database and JWT secret
```bash
openssl rand -base64 32
```

2. **Limit Network Exposure**: Only expose necessary ports
```yaml
# Don't expose database port in production
# ports:
#   - "5432:5432"
```

3. **Use SSL/TLS**: Configure Nginx with SSL certificates
```bash
# Generate self-signed certificate for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
```

4. **Regular Updates**: Keep Docker images updated
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

5. **Secrets Management**: Use Docker secrets or environment files
```bash
# Don't commit .env files to version control
echo ".env" >> .gitignore
```

6. **Resource Limits**: Set memory and CPU limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

## Performance Optimization

### Backend Scaling

Increase the number of Uvicorn workers:
```yaml
command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

### Database Tuning

Optimize PostgreSQL settings:
```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_MAX_CONNECTIONS: 100
```

### Caching

Enable Redis for caching (optional):
```yaml
redis:
  image: redis:7-alpine
  container_name: climate_redis
  ports:
    - "6379:6379"
```

## Backup and Recovery

### Automated Backups

Create a backup script:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec db pg_dump -U user climate_prod > backups/backup_$DATE.sql
find backups/ -mtime +7 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh
```

### Disaster Recovery

1. Stop services:
```bash
docker-compose -f docker-compose.prod.yml down
```

2. Restore database:
```bash
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec -T db psql -U user climate_prod < backup.sql
```

3. Start all services:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Upgrading

### Application Updates

1. Pull latest code:
```bash
git pull origin main
```

2. Rebuild and restart:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Run migrations:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Database Migrations

1. Create migration:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic revision --autogenerate -m "description"
```

2. Review migration file in `backend/alembic/versions/`

3. Apply migration:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Production Deployment Checklist

- [ ] Set strong passwords for database and JWT secret
- [ ] Configure SSL certificates for Nginx
- [ ] Set up email/Slack alerts
- [ ] Configure backup schedule
- [ ] Set resource limits for containers
- [ ] Enable monitoring and alerting
- [ ] Test health check endpoints
- [ ] Verify pipeline schedule
- [ ] Test manual pipeline trigger
- [ ] Review and adjust log retention
- [ ] Set up external monitoring (e.g., Prometheus, Grafana)
- [ ] Document custom configuration
- [ ] Test disaster recovery procedure

## Support and Resources

- **Documentation**: See `docs/` directory for detailed guides
- **API Documentation**: http://localhost:8000/docs
- **Health Checks**: http://localhost:8080/health
- **Metrics**: http://localhost:9090/metrics

For issues and questions, refer to the project README or contact the development team.
