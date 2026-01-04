# Testing Instructions - Automated Forecast Pipeline

## ⚠️ IMPORTANT: Test Verification Required

**Status**: Tests have been written but not fully verified to pass.  
**Action Required**: Run all tests and fix any failures before production deployment.

## Test Suite Overview

### Property-Based Tests (41 tests)
- `test_incremental_manager_properties.py` - 4 tests
- `test_incremental_manager_unit.py` - 3+ tests
- `test_orchestrator_properties.py` - 5 tests
- `test_retry_handler_properties.py` - 6 tests ⚠️ NOT VERIFIED
- `test_alert_service_properties.py` - 7 tests ⚠️ NOT VERIFIED
- `test_scheduler_properties.py` - 7 tests ⚠️ NOT VERIFIED
- `test_monitoring_service_properties.py` - 5 tests ⚠️ NOT VERIFIED
- `test_pipeline_freshness_properties.py` - 4 tests

### Integration Tests (8 tests)
- `test_pipeline_integration.py` - 8 tests ⚠️ NOT VERIFIED

## Prerequisites

### 1. Database Setup
```bash
# Ensure PostgreSQL is running
docker-compose up -d db

# Run migrations
cd backend
alembic upgrade head
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit .env with test database URL
DATABASE_URL=postgresql://user:pass@localhost:5432/climate_test
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio hypothesis
```

## Running Tests

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Property Tests Only
```bash
python -m pytest tests/test_*_properties.py -v
```

### Run Integration Tests Only
```bash
python -m pytest tests/test_pipeline_integration.py -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_retry_handler_properties.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=app.services.pipeline --cov-report=html
open htmlcov/index.html
```

## Known Issues to Fix

### 1. Configuration Validation Error
**Issue**: Settings class was rejecting extra environment variables  
**Fix Applied**: Added `extra = "ignore"` to Settings.Config  
**Verification Needed**: Run tests to confirm fix works

### 2. Test Timeouts
**Issue**: Some property tests may hang due to actual delays  
**Potential Fix**: Reduce delay times in tests or use mocking  
**Files to Check**:
- `test_retry_handler_properties.py` - Uses actual time.sleep()
- `test_scheduler_properties.py` - May have timing issues

### 3. Missing Test Database
**Issue**: Tests may fail if test database doesn't exist  
**Fix**: Create test database before running tests
```sql
CREATE DATABASE climate_test;
```

### 4. Missing Fixtures
**Issue**: Some tests reference fixtures that may not be properly configured  
**Fix**: Check `backend/tests/conftest.py` for fixture definitions

## Test Execution Checklist

- [ ] Database is running and accessible
- [ ] Test database exists and migrations are applied
- [ ] Environment variables are configured
- [ ] All dependencies are installed
- [ ] Run: `pytest tests/test_retry_handler_properties.py -v`
- [ ] Run: `pytest tests/test_alert_service_properties.py -v`
- [ ] Run: `pytest tests/test_scheduler_properties.py -v`
- [ ] Run: `pytest tests/test_monitoring_service_properties.py -v`
- [ ] Run: `pytest tests/test_pipeline_integration.py -v`
- [ ] Run: `pytest tests/test_orchestrator_properties.py -v`
- [ ] Run: `pytest tests/test_incremental_manager_properties.py -v`
- [ ] Run: `pytest tests/test_pipeline_freshness_properties.py -v`
- [ ] All tests pass ✓
- [ ] Coverage report generated
- [ ] Coverage > 80% for pipeline services

## Debugging Failed Tests

### View Detailed Output
```bash
python -m pytest tests/test_file.py -vv -s
```

### Run Single Test
```bash
python -m pytest tests/test_file.py::test_function_name -v
```

### Show Print Statements
```bash
python -m pytest tests/test_file.py -v -s
```

### Stop on First Failure
```bash
python -m pytest tests/ -x
```

### Run Last Failed Tests
```bash
python -m pytest --lf
```

## Common Test Failures and Solutions

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'app'`  
**Solution**: Ensure PYTHONPATH includes backend directory
```bash
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

### Database Connection Errors
**Error**: `could not connect to server`  
**Solution**: Start database and verify connection string
```bash
docker-compose up -d db
psql $DATABASE_URL -c "SELECT 1"
```

### Fixture Errors
**Error**: `fixture 'db' not found`  
**Solution**: Check conftest.py has fixture defined
```python
@pytest.fixture
def db():
    # fixture implementation
```

### Async Test Errors
**Error**: `RuntimeError: Event loop is closed`  
**Solution**: Ensure pytest-asyncio is installed and tests use `@pytest.mark.asyncio`

### Hypothesis Errors
**Error**: `hypothesis.errors.Flaky`  
**Solution**: Test found inconsistent behavior - fix the code or adjust test

## Test Maintenance

### Adding New Tests
1. Create test file: `tests/test_feature_properties.py`
2. Add property-based tests using Hypothesis
3. Tag with feature name and property number
4. Reference requirements validated
5. Run tests to verify they pass
6. Update this documentation

### Updating Existing Tests
1. Make changes to test file
2. Run affected tests
3. Verify all tests still pass
4. Update test documentation if behavior changed

## CI/CD Integration

### GitHub Actions (Recommended)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio hypothesis pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app.services.pipeline
```

## Next Steps

1. **CRITICAL**: Run all tests and fix failures
2. Set up CI/CD to run tests automatically
3. Achieve >80% code coverage
4. Add more edge case tests as needed
5. Document any test-specific configuration

## Support

If tests fail and you need help:
1. Check error message carefully
2. Review this troubleshooting guide
3. Check test file for comments
4. Review implementation code
5. Ask team for help with specific error

---

**Last Updated**: November 27, 2024  
**Status**: Tests written, verification pending  
**Priority**: HIGH - Must verify before production deployment
