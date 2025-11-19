# Quick Start Guide - Interactive Dashboard System

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- PostgreSQL 15+ (if not using Docker)

## Quick Start with Docker (Recommended)

### 1. Clone and Navigate
```bash
cd dashboard
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, change JWT_SECRET and database password
```

### 3. Start Services
```bash
# Start all services (database, backend, frontend)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Create initial admin user (optional)
docker-compose -f docker-compose.dev.yml exec backend python -c "
from app.core.database import SessionLocal
from app.services.auth_service import create_user
from app.schemas.user import UserCreate

db = SessionLocal()
user = create_user(db, UserCreate(
    username='admin',
    email='admin@example.com',
    password='admin123',
    role='admin'
))
print(f'Created admin user: {user.username}')
"
```

### 5. Access the Application
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000 (when implemented)

### 6. Test the API
```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "role": "analyst"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

# Use the returned token for authenticated requests
TOKEN="<your_token_here>"

# Get executive dashboard
curl -X GET http://localhost:8000/api/dashboard/executive \
  -H "Authorization: Bearer $TOKEN"
```

## Local Development (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database URL

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend Setup (Coming Soon)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Run Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## Common Tasks

### Create Database Migration
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Add Sample Data
```bash
# You can use the API or create a script
# Example: Load trigger events from CSV
docker-compose -f docker-compose.dev.yml exec backend python scripts/load_data.py
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
```

### Stop Services
```bash
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.dev.yml down -v
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps

# Check database logs
docker-compose -f docker-compose.dev.yml logs db

# Restart database
docker-compose -f docker-compose.dev.yml restart db
```

### Backend Not Starting
```bash
# Check backend logs
docker-compose -f docker-compose.dev.yml logs backend

# Common issues:
# 1. Database not ready - wait a few seconds and retry
# 2. Port 8000 already in use - stop other services
# 3. Environment variables missing - check .env file
```

### Tests Failing
```bash
# Make sure you're in the backend directory
cd backend

# Install test dependencies
pip install -r requirements.txt

# Run tests with verbose output
pytest tests/ -v -s
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Create Test Data**: Use the API to create sample trigger events, climate data, etc.
3. **Run Tests**: Verify everything works with `pytest`
4. **Frontend Development**: Begin implementing React dashboards
5. **Customize**: Modify services and endpoints for your specific needs

## API Authentication

All endpoints except `/api/auth/register` and `/api/auth/login` require authentication.

1. Register or login to get a JWT token
2. Include the token in the Authorization header:
   ```
   Authorization: Bearer <your_token>
   ```
3. Tokens expire after 24 hours (configurable in .env)

## Roles and Permissions

- **admin**: Full access to all endpoints, user management
- **analyst**: Read/write access to data, models, triggers
- **viewer**: Read-only access to dashboards and data

## Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review logs: `docker-compose logs -f`
3. Check the design document: `.kiro/specs/interactive-dashboard-system/design.md`
4. Review test files for usage examples: `backend/tests/`
