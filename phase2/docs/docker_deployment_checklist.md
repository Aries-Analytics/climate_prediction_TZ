# Docker Deployment Verification Checklist

**Task**: 28. Final Checkpoint - Complete system integration  
**Date**: November 21, 2025  
**Status**: In Progress

---

## Pre-Deployment Checklist

### 1. Environment Configuration ✓

- [ ] `.env` file exists in backend directory
- [ ] Database credentials configured
- [ ] JWT secret configured (not default)
- [ ] CORS origins configured
- [ ] All required environment variables set

### 2. Docker Files ✓

- [x] `backend/Dockerfile` exists
- [x] `frontend/Dockerfile` exists
- [x] `docker-compose.dev.yml` exists
- [x] `docker-compose.prod.yml` exists
- [ ] `nginx/nginx.conf` exists (for production)

### 3. Dependencies ✓

- [x] Docker installed and running
- [x] Docker Compose installed
- [ ] Required ports available (80, 443, 3000, 5432, 8000)

---

## Deployment Steps

### Step 1: Build Docker Images

```bash
# Development
docker-compose -f docker-compose.dev.yml build

# Production
docker-compose -f docker-compose.prod.yml build
```

### Step 2: Start Services

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Step 3: Verify Services

```bash
# Check running containers
docker-compose -f docker-compose.dev.yml ps

# Check logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Step 4: Run Database Migrations

```bash
# Development
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Production
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 5: Create Initial Admin User

```bash
# Development
docker-compose -f docker-compose.dev.yml exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created')
"
```

---

## Verification Tests

### Automated Verification

Run the automated verification script:

```bash
python verify_docker_deployment.py
```

### Manual Verification

#### 1. Backend Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

#### 2. Frontend Accessibility

```bash
curl http://localhost:3000
# Expected: HTML content
```

#### 3. Database Connection

```bash
docker-compose -f docker-compose.dev.yml exec db psql -U user -d climate_dev -c "SELECT 1;"
# Expected: 1 row returned
```

#### 4. API Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"Test123!","role":"analyst"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'
# Expected: {"access_token": "...", "token_type": "bearer"}
```

#### 5. Dashboard Endpoints

```bash
# Get token first, then:
TOKEN="your_token_here"

# Executive Dashboard
curl http://localhost:8000/api/dashboard/executive \
  -H "Authorization: Bearer $TOKEN"

# Triggers
curl http://localhost:8000/api/triggers \
  -H "Authorization: Bearer $TOKEN"

# Climate Data
curl "http://localhost:8000/api/climate/timeseries?variable=temperature" \
  -H "Authorization: Bearer $TOKEN"

# Models
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer $TOKEN"

# Risk Portfolio
curl http://localhost:8000/api/risk/portfolio \
  -H "Authorization: Bearer $TOKEN"
```

---

## Dashboard Functionality Tests

### Executive Dashboard
- [ ] KPI cards display correctly
- [ ] Loss ratio chart renders
- [ ] Trigger distribution chart renders
- [ ] Sustainability status shows
- [ ] Data refreshes on date range change

### Model Performance Dashboard
- [ ] Model list loads
- [ ] Model metrics display
- [ ] Feature importance chart renders
- [ ] Model comparison works
- [ ] Drift detection shows

### Triggers Dashboard
- [ ] Trigger events table loads
- [ ] Timeline view renders
- [ ] Filters work correctly
- [ ] Date range selection works
- [ ] Export functionality works

### Climate Insights Dashboard
- [ ] Time series chart renders
- [ ] Multiple variables can be selected
- [ ] Anomaly detection works
- [ ] Correlation matrix displays
- [ ] Seasonal patterns show

### Risk Management Dashboard
- [ ] Portfolio metrics display
- [ ] Risk distribution charts render
- [ ] Scenario analysis form works
- [ ] Recommendations display
- [ ] Early warnings show

---

## Performance Tests

### Response Time Benchmarks

```bash
# Install Apache Bench
# sudo apt-get install apache2-utils

# Test API endpoint
ab -n 100 -c 10 http://localhost:8000/api/dashboard/executive \
  -H "Authorization: Bearer $TOKEN"

# Expected: < 500ms average response time
```

### Load Testing

```bash
# Test with 1000 requests, 50 concurrent
ab -n 1000 -c 50 http://localhost:8000/health

# Expected: No errors, < 1s average response time
```

---

## Security Verification

### 1. Authentication Required

```bash
# Should return 401 Unauthorized
curl http://localhost:8000/api/dashboard/executive
```

### 2. CORS Configuration

```bash
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS http://localhost:8000/api/dashboard/executive
# Expected: CORS headers present
```

### 3. Security Headers

```bash
curl -I http://localhost:8000/health
# Expected: X-Content-Type-Options, X-Frame-Options headers
```

### 4. Rate Limiting

```bash
# Make rapid requests
for i in {1..150}; do
  curl http://localhost:8000/health &
done
wait
# Expected: Some requests return 429 Too Many Requests
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs

# Check specific service
docker-compose -f docker-compose.dev.yml logs backend

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.dev.yml ps db

# Check database logs
docker-compose -f docker-compose.dev.yml logs db

# Connect to database manually
docker-compose -f docker-compose.dev.yml exec db psql -U user -d climate_dev
```

### Port Conflicts

```bash
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5432

# Kill process or change ports in docker-compose.yml
```

### Build Failures

```bash
# Clean build
docker-compose -f docker-compose.dev.yml build --no-cache

# Remove old images
docker system prune -a
```

---

## Cleanup

### Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

### Remove Volumes (WARNING: Deletes data)

```bash
docker-compose -f docker-compose.dev.yml down -v
```

### Remove Images

```bash
docker-compose -f docker-compose.dev.yml down --rmi all
```

---

## Success Criteria

### All Tests Must Pass ✓

- [x] Backend service starts successfully
- [x] Frontend service starts successfully
- [x] Database connection established
- [ ] Authentication system works
- [ ] All 5 dashboards load without errors
- [ ] API endpoints return valid data
- [ ] Security measures in place
- [ ] Performance meets requirements (<500ms response time)

### Documentation Complete ✓

- [x] API documentation available
- [x] Deployment guide available
- [x] User guide available
- [x] Troubleshooting guide available

### Production Ready ✓

- [ ] Environment variables configured
- [ ] Security headers configured
- [ ] HTTPS configured (production)
- [ ] Monitoring configured
- [ ] Backup strategy in place

---

## Sign-Off

**Verified By**: _________________  
**Date**: _________________  
**Status**: ☐ Passed ☐ Failed ☐ Needs Review  
**Notes**: _________________

---

**Next Steps After Verification**:
1. User acceptance testing
2. Performance optimization if needed
3. Production deployment
4. User training
5. Go-live

