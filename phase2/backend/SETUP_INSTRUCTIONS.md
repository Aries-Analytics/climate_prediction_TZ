# Backend Setup Instructions

## Quick Setup (Recommended)

### Windows
```bash
cd backend
setup.bat
```

### Linux/Mac
```bash
cd backend
chmod +x setup.sh
./setup.sh
```

## Manual Setup

### 1. Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - DATABASE_URL (if not using Docker)
# - JWT_SECRET (change to a secure random string)
```

### 4. Set Up Database

**Option A: Using Docker (Recommended)**
```bash
# From the dashboard directory
cd ..
docker-compose -f docker-compose.dev.yml up -d db

# Wait for database to be ready, then run migrations
cd backend
alembic upgrade head
```

**Option B: Local PostgreSQL**
```bash
# Make sure PostgreSQL is installed and running
# Create database
createdb climate_dev

# Update DATABASE_URL in .env
# DATABASE_URL=postgresql://user:password@localhost:5432/climate_dev

# Run migrations
alembic upgrade head
```

**Option C: SQLite (for testing only)**
```bash
# Update DATABASE_URL in .env
# DATABASE_URL=sqlite:///./test.db

# Run migrations
alembic upgrade head
```

### 5. Run Tests

```bash
# Make sure virtual environment is activated
pytest tests/ -v --cov=app --cov-report=term-missing
```

Expected output: All tests should pass

### 6. Start Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Troubleshooting

### ModuleNotFoundError: No module named 'fastapi'

**Solution:** Make sure you've activated the virtual environment and installed dependencies:
```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

### Database Connection Error

**Solution:** Check your DATABASE_URL in .env file:
```bash
# For Docker
DATABASE_URL=postgresql://user:pass@localhost:5432/climate_dev

# For local PostgreSQL
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/climate_dev

# For SQLite (testing only)
DATABASE_URL=sqlite:///./test.db
```

### Alembic Migration Errors

**Solution:** Make sure database is running and accessible:
```bash
# Check if database is running (Docker)
docker-compose -f ../docker-compose.dev.yml ps

# Or check local PostgreSQL
psql -l

# Reset migrations if needed
alembic downgrade base
alembic upgrade head
```

### Import Errors in Tests

**Solution:** Make sure you're in the backend directory and virtual environment is activated:
```bash
cd backend
# Activate venv
pytest tests/ -v
```

### Port 8000 Already in Use

**Solution:** Stop other services using port 8000 or use a different port:
```bash
# Use different port
uvicorn app.main:app --reload --port 8001

# Or find and kill process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or find and kill process (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

## Verification

After setup, verify everything is working:

```bash
# 1. Check Python version
python --version  # Should be 3.9+

# 2. Check installed packages
pip list | grep fastapi

# 3. Run verification script
python verify_setup.py

# 4. Run tests
pytest tests/ -v

# 5. Start server and check health
uvicorn app.main:app --reload
# Visit http://localhost:8000/health
```

## Next Steps

Once setup is complete:

1. **Explore API**: Visit http://localhost:8000/docs
2. **Create Test User**: Use the /api/auth/register endpoint
3. **Test Authentication**: Login and get a JWT token
4. **Try Endpoints**: Use the token to access protected endpoints
5. **Load Sample Data**: Create some test data via the API

## Development Workflow

```bash
# 1. Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Start development server
uvicorn app.main:app --reload

# 3. In another terminal, run tests
pytest tests/ -v --cov=app

# 4. Make changes to code
# Server will auto-reload

# 5. Run tests again to verify
pytest tests/ -v
```

## Docker Alternative

If you prefer using Docker for everything:

```bash
# From dashboard directory
docker-compose -f docker-compose.dev.yml up

# Run tests in container
docker-compose -f docker-compose.dev.yml exec backend pytest tests/ -v

# Access logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review error messages carefully
3. Check the logs
4. Verify your environment configuration
5. Make sure all dependencies are installed
