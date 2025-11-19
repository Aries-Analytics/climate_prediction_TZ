# How to Run Tests for Tasks 1-10

## Prerequisites

The dependencies are currently being installed. Once complete, follow these steps:

## Step 1: Verify Installation

```bash
cd backend
pip list | findstr fastapi
```

You should see fastapi, sqlalchemy, pytest, and other packages listed.

## Step 2: Run All Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Or use the batch script
run_tests.bat
```

## Step 3: Expected Results

All tests should pass:
- ✅ test_auth.py - 12 tests (authentication and authorization)
- ✅ test_models.py - 6 tests (model performance services)
- ✅ test_triggers.py - 7 tests (trigger events services)
- ✅ test_dashboard.py - 6 tests (dashboard services)

**Total: 31+ tests**

## What the Tests Validate

### Authentication (Task 3)
- User registration and login
- Password hashing with bcrypt
- JWT token generation and validation
- Protected endpoint access
- Role-based access control

### Database Models (Task 2)
- All 6 models work correctly
- Proper relationships and indexes
- SQLAlchemy ORM functionality

### Dashboard Services (Task 4)
- Executive KPIs calculation
- Trigger rate calculations
- Loss ratio calculations
- Sustainability status

### Model Performance (Task 5)
- Model metrics retrieval
- Model comparison
- Drift detection
- Feature importance

### Trigger Events (Task 6)
- Event retrieval with filters
- Timeline generation
- CSV export

## If Tests Fail

1. **Check database**: Tests use SQLite in-memory, no setup needed
2. **Check imports**: Make sure all dependencies are installed
3. **Check Python version**: Requires Python 3.9+
4. **View detailed errors**: Run with `-v -s` flags

```bash
pytest tests/ -v -s
```

## Coverage Report

After running tests, view the HTML coverage report:

```bash
# Open in browser
start htmlcov\index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

Target: >80% code coverage

## Quick Verification

To quickly verify the setup is correct:

```bash
python verify_setup.py
```

This will check that all required files exist.

## Summary

Once dependencies finish installing and tests pass, **Tasks 1-10 are complete** and the backend is ready for frontend integration!
