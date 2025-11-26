# Tanzania Climate Prediction API - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Health Checks](#health-checks)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum
- **Network**: Internet connection for initial setup

### Software Requirements

- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.9+ (for manual deployment)
- **PostgreSQL**: 13+ (for manual deployment)
- **Redis**: 6.0+ (optional, for caching)
- **Git**: For cloning the repository

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/tanzania-climate-api.git
cd tanzania-climate-api
```

### 2. Create Environment File

Create a `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env
```

### 3. Configure Environment Variables

Edit the `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://climate_user:secure_password@localhost:5432/climate_db

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# File Paths
OUTPUTS_DIR=../outputs
MODELS_DIR=../outputs/models

# Logging
LOG_LEVEL=INFO

# Redis Cache (Optional)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300
CACHE_ENABLED=true

# Application Settings
APP_NAME=Tanzania Climate Prediction API
APP_VERSION=1.0.0
DEBUG=false
```

**Important**: Change all default passwords and secrets in production!

---

## Docker Deployment

### Quick Start with Docker Compose

The easiest way to deploy the application is using Docker Compose.

#### 1. Build and Start Services

```bash
# From the project root directory
docker-compose -f docker-compose.prod.yml up -d
```

This will start:
- Backend API (FastAPI)
- PostgreSQL database
- Redis cache
- Nginx reverse proxy

#### 2. Check Service Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

#### 3. View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

#### 4. Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### 5. Create Admin User

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin
```

#### 6. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Docker Compose Configuration

The `docker-compose.prod.yml` file includes:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://climate_user:${DB_PASSWORD}@db:5432/climate_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./outputs:/app/outputs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=climate_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=climate_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### Stopping Services

```bash
docker-compose -f docker-compose.prod.yml down
```

To also remove volumes:

```bash
docker-compose -f docker-compose.prod.yml down -v
```

---

## Manual Deployment

### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE climate_db;
CREATE USER climate_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE climate_db TO climate_user;
\q
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Install Redis (Optional)

```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 5. Start the Application

#### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode with Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 6. Set Up Systemd Service (Linux)

Create `/etc/systemd/system/climate-api.service`:

```ini
[Unit]
Description=Tanzania Climate Prediction API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/climate-api/backend
Environment="PATH=/opt/climate-api/backend/venv/bin"
ExecStart=/opt/climate-api/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable climate-api
sudo systemctl start climate-api
sudo systemctl status climate-api
```

---

## Database Setup

### Running Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history

# Create new migration
alembic revision --autogenerate -m "Description of changes"
```

### Database Backup

```bash
# Backup
pg_dump -U climate_user -h localhost climate_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U climate_user -h localhost climate_db < backup_20240315.sql
```

### Database Optimization

```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim storage
VACUUM ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

---

## Configuration

### Nginx Configuration

Create `/etc/nginx/sites-available/climate-api`:

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /opt/climate-api/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/climate-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

Using Let's Encrypt:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "api"}
```

### Readiness Check

```bash
curl http://localhost:8000/health/ready
```

Expected response:
```json
{"status": "ready", "database": "connected"}
```

### Monitoring Script

Create `health_check.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000"

# Check API health
if curl -f -s "${API_URL}/health" > /dev/null; then
    echo "✓ API is healthy"
else
    echo "✗ API is down"
    exit 1
fi

# Check database connectivity
if curl -f -s "${API_URL}/health/ready" > /dev/null; then
    echo "✓ Database is connected"
else
    echo "✗ Database connection failed"
    exit 1
fi

echo "All health checks passed"
```

---

## Monitoring

### Application Logs

```bash
# View logs
tail -f /var/log/climate-api/app.log

# With Docker
docker-compose logs -f backend
```

### Database Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 minutes';

-- Database size
SELECT pg_size_pretty(pg_database_size('climate_db'));
```

### Redis Monitoring

```bash
redis-cli INFO
redis-cli MONITOR
```

### Performance Metrics

Monitor these key metrics:

- **Response Time**: < 500ms for 95th percentile
- **Error Rate**: < 1%
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%
- **Database Connections**: < 80% of max

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Problem**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection settings
psql -U climate_user -h localhost -d climate_db

# Verify DATABASE_URL in .env
```

#### 2. Migration Errors

**Problem**: `alembic.util.exc.CommandError: Can't locate revision`

**Solution**:
```bash
# Reset migrations
alembic stamp head

# Or start fresh
alembic downgrade base
alembic upgrade head
```

#### 3. Redis Connection Errors

**Problem**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Disable caching if Redis is not needed
# Set CACHE_ENABLED=false in .env
```

#### 4. Permission Errors

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Fix file permissions
sudo chown -R www-data:www-data /opt/climate-api
sudo chmod -R 755 /opt/climate-api

# Fix log directory
sudo mkdir -p /var/log/climate-api
sudo chown www-data:www-data /var/log/climate-api
```

#### 5. High Memory Usage

**Problem**: Application consuming too much memory

**Solution**:
```bash
# Reduce number of workers
# In gunicorn command, use fewer workers
--workers 2

# Increase worker timeout
--timeout 120

# Monitor memory
htop
```

### Debug Mode

Enable debug mode for detailed error messages:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

**Warning**: Never enable debug mode in production!

---

## Security Considerations

### 1. Change Default Credentials

- Update `JWT_SECRET` to a strong random value
- Change database passwords
- Use strong passwords for all accounts

### 2. Enable HTTPS

- Always use HTTPS in production
- Obtain SSL certificates from Let's Encrypt or a trusted CA
- Configure SSL properly in Nginx

### 3. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. Database Security

```sql
-- Restrict database access
-- In pg_hba.conf, use:
host    climate_db    climate_user    127.0.0.1/32    md5

-- Revoke public schema privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

### 5. Regular Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull
```

### 6. Backup Strategy

- Daily database backups
- Weekly full system backups
- Store backups off-site
- Test restore procedures regularly

---

## Production Checklist

Before deploying to production:

- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Test health check endpoints
- [ ] Review and apply security headers
- [ ] Configure rate limiting
- [ ] Set DEBUG=false
- [ ] Test disaster recovery procedures
- [ ] Document custom configurations
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling (if using cloud)
- [ ] Review CORS settings
- [ ] Enable audit logging

---

## Support

For deployment support:
- Email: devops@example.com
- Documentation: https://docs.example.com
- Issue Tracker: https://github.com/your-org/tanzania-climate-api/issues
