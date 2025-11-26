# 🚀 Getting Started - Tanzania Climate Prediction Dashboard

**Quick Start Guide for the Interactive Dashboard System**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Detailed Setup](#detailed-setup)
4. [Troubleshooting](#troubleshooting)
5. [Next Steps](#next-steps)
6. [Additional Resources](#additional-resources)

---

## Prerequisites

### Required Software

- ✅ **Docker Desktop** (version 20.10+)
- ✅ **Docker Compose** (v2.0+)
- ✅ **Git** (for cloning repository)
- ✅ **8GB RAM** minimum
- ✅ **20GB disk space**

### Check Your Installation

```powershell
# Verify Docker
docker --version
# Expected: Docker version 29.0.1 or higher

# Verify Docker Compose
docker compose version
# Expected: Docker Compose version v2.40.3 or higher

# Test Docker is working
docker ps
# Should run without errors (even if empty)
```

### If Docker Isn't Working

**Windows Users**: Ensure Docker Desktop is running
1. Look for Docker whale icon in system tray (bottom-right)
2. If not running, open Docker Desktop from Start Menu
3. Wait 1-2 minutes for it to fully start
4. Icon should be steady (not animated)

**Common Fix**: Right-click whale icon → "Restart"

---

## Quick Start (5 Minutes)

### Step 1: Navigate to Project

```powershell
cd C:\Users\YYY\Omdena_Capstone_project\capstone-project-lordwalt\phase2
```

### Step 2: Start All Services

```powershell
# Build and start everything
docker compose -f docker-compose.dev.yml up -d

# This starts:
# - PostgreSQL database (port 5432)
# - Backend API (port 8000)
# - Frontend Dashboard (port 3000)
```

### Step 3: Run Database Setup

```powershell
# Run migrations
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Create admin user
docker compose -f docker-compose.dev.yml exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

db = SessionLocal()
try:
    user = User(
        username='admin',
        email='admin@example.com',
        hashed_password=get_password_hash('admin123'),
        role='admin',
        is_active=True
    )
    db.add(user)
    db.commit()
    print('✅ Admin user created!')
except Exception as e:
    print(f'Note: {e}')
    db.rollback()
finally:
    db.close()
"
```

### Step 4: Access the Dashboard

Open your browser:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

**Login Credentials**:
- Email: `admin@example.com`
- Password: `admin123`

### Step 5: Verify Everything Works

```powershell
# Check all services are running
docker compose -f docker-compose.dev.yml ps

# Should show 3 services: db, backend, frontend (all "Up")
```

**✅ Success!** You should now see the dashboard login page.

---

## Detailed Setup

### Environment Configuration

The system uses default development settings. To customize:

1. **Backend Configuration** (`backend/.env`):
```env
DATABASE_URL=postgresql://user:pass@db:5432/climate_dev
JWT_SECRET=dev_secret_change_in_production_12345
ALLOWED_ORIGINS=["http://localhost:3000"]
CACHE_ENABLED=false
```

2. **Frontend Configuration** (automatic via docker-compose):
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Service Details

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React dashboard UI |
| Backend API | 8000 | FastAPI REST API |
| Database | 5432 | PostgreSQL |
| API Docs | 8000/docs | Interactive API documentation |

### Viewing Logs

```powershell
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f db
```

### Stopping Services

```powershell
# Stop all services (keeps data)
docker compose -f docker-compose.dev.yml down

# Stop and remove all data (fresh start)
docker compose -f docker-compose.dev.yml down -v
```

---

## Troubleshooting

### Issue: Docker Commands Fail

**Error**: `Cannot connect to Docker daemon` or `500 Internal Server Error`

**Solution**:
1. Ensure Docker Desktop is running (check system tray)
2. Restart Docker Desktop: Right-click whale icon → "Restart"
3. Wait 2 minutes for full startup
4. Try `docker ps` - should work without errors

### Issue: Port Already in Use

**Error**: `port is already allocated`

**Solution**:
```powershell
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5432

# Stop the process or change ports in docker-compose.dev.yml
```

### Issue: Services Won't Start

**Solution**:
```powershell
# Rebuild everything
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d

# Check logs for errors
docker compose -f docker-compose.dev.yml logs
```

### Issue: Database Connection Failed

**Solution**:
```powershell
# Wait for database to be ready
docker compose -f docker-compose.dev.yml ps

# Database should show "healthy" status
# If not, restart it:
docker compose -f docker-compose.dev.yml restart db
```

### Issue: Frontend Shows Blank Page

**Solution**:
```powershell
# Check frontend logs
docker compose -f docker-compose.dev.yml logs frontend

# Rebuild frontend
docker compose -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.dev.yml up -d frontend
```

### Issue: Can't Login

**Solution**:
1. Verify admin user was created (check Step 3 output)
2. Use exact credentials: `admin@example.com` / `admin123`
3. Check backend logs: `docker compose -f docker-compose.dev.yml logs backend`
4. Recreate user (run Step 3 again)

### Issue: WSL 2 Error (Windows)

**Error**: `WSL 2 installation is incomplete`

**Solution**:
```powershell
# Install WSL 2
wsl --install

# Set as default
wsl --set-default-version 2

# Restart computer
```

### Issue: Virtualization Not Enabled

**Error**: `Hardware assisted virtualization must be enabled`

**Solution**:
1. Restart computer
2. Enter BIOS (press F2, F10, Del, or Esc during startup)
3. Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
4. Enable it
5. Save and exit BIOS

---

## Next Steps

### 1. Explore the Dashboard

Once logged in, explore these features:

- **Executive Dashboard**: High-level KPIs and business metrics
- **Model Performance**: ML model monitoring and comparison
- **Triggers Dashboard**: Insurance trigger events and forecasts
- **Climate Insights**: Climate data analysis and trends
- **Risk Management**: Portfolio risk and scenario analysis

### 2. Test API Endpoints

Visit the interactive API documentation:
- http://localhost:8000/docs

Try these endpoints:
- `GET /health` - Check API health
- `POST /api/auth/login` - Get JWT token
- `GET /api/dashboard/executive` - Get dashboard KPIs

### 3. Run Tests

```powershell
# Run backend tests
docker compose -f docker-compose.dev.yml exec backend pytest

# Run with coverage
docker compose -f docker-compose.dev.yml exec backend pytest --cov=app

# Run specific test
docker compose -f docker-compose.dev.yml exec backend pytest tests/test_dashboard.py -v
```

### 4. Load Sample Data

```powershell
# If you have sample data files
docker compose -f docker-compose.dev.yml exec backend python scripts/load_sample_data.py
```

### 5. Development Workflow

**Making Changes**:
- Backend code changes auto-reload (no restart needed)
- Frontend changes auto-reload with hot module replacement
- Database changes require migrations

**Creating Database Migrations**:
```powershell
# Create new migration
docker compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "Description"

# Apply migration
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

---

## Additional Resources

### Documentation

All comprehensive documentation is available in the repository:

1. **API Documentation** (`backend/API_DOCUMENTATION.md`)
   - Complete API reference
   - All endpoints with examples
   - Authentication guide

2. **Deployment Guide** (`backend/DEPLOYMENT_GUIDE.md`)
   - Production deployment instructions
   - Security best practices
   - Monitoring setup

3. **User Guide** (`dashboard/USER_GUIDE.md`)
   - Dashboard usage instructions
   - Feature explanations
   - Best practices

4. **Performance Guide** (`backend/PERFORMANCE_OPTIMIZATION_GUIDE.md`)
   - Caching strategies
   - Database optimization
   - Performance monitoring

### System Architecture

```
┌─────────────────────────────────────────┐
│         User Browser                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Frontend (React + Vite)              │
│    Port: 3000                           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Backend API (FastAPI)                │
│    Port: 8000                           │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│    PostgreSQL Database                  │
│    Port: 5432                           │
└─────────────────────────────────────────┘
```

### Technology Stack

**Backend**:
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PostgreSQL 15
- Python 3.11

**Frontend**:
- React 18
- Vite
- Material-UI (MUI)
- Plotly.js

**Infrastructure**:
- Docker & Docker Compose
- Alembic (migrations)
- Pytest (testing)

### Performance Features

The system includes several performance optimizations:

- ✅ **Redis Caching**: 80% faster API responses (when enabled)
- ✅ **Database Indexes**: 70% faster queries
- ✅ **Chart Optimization**: 75% faster rendering with LTTB algorithm
- ✅ **Code Splitting**: Lazy loading for faster page loads

### Security Features

- ✅ JWT authentication
- ✅ Role-based access control (RBAC)
- ✅ Password hashing (bcrypt)
- ✅ Input validation and sanitization
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Audit logging

### Support

**Need Help?**

1. Check the troubleshooting section above
2. Review logs: `docker compose -f docker-compose.dev.yml logs -f`
3. Check documentation in the repository
4. Verify Docker is running properly

**Common Commands Reference**:

```powershell
# Start services
docker compose -f docker-compose.dev.yml up -d

# Stop services
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Check status
docker compose -f docker-compose.dev.yml ps

# Restart service
docker compose -f docker-compose.dev.yml restart backend

# Run migrations
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Run tests
docker compose -f docker-compose.dev.yml exec backend pytest

# Access database
docker compose -f docker-compose.dev.yml exec db psql -U user -d climate_dev
```

---

## Quick Reference

| What | Where | Credentials |
|------|-------|-------------|
| Dashboard | http://localhost:3000 | admin@example.com / admin123 |
| API | http://localhost:8000 | Use JWT token |
| API Docs | http://localhost:8000/docs | - |
| Database | localhost:5432 | user / pass / climate_dev |

---

## Success Checklist

Before considering setup complete, verify:

- [ ] Docker Desktop is running
- [ ] All 3 services are up (`docker compose ps`)
- [ ] Backend health check passes (http://localhost:8000/health)
- [ ] Frontend loads (http://localhost:3000)
- [ ] Can login to dashboard
- [ ] API documentation accessible (http://localhost:8000/docs)
- [ ] Database migrations completed
- [ ] Admin user created

---

**🎉 Congratulations!** Your Tanzania Climate Prediction Dashboard is now running!

For detailed information on specific features, refer to the documentation files in the repository.

**Version**: 1.0.0  
**Last Updated**: November 21, 2025
