# Testing Reference

**Last Updated**: January 5, 2026  
**Version**: 2.0  
**Status**: ✅ Production Ready

---

## Overview

The Tanzania Climate Intelligence Platform employs a comprehensive testing strategy combining unit tests, integration tests, and property-based tests to ensure system reliability and correctness. The test suite provides 80%+ code coverage with over 100 test cases across all system components.

### Testing Philosophy

**Multi-Layered Approach**:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows
- **Property-Based Tests**: Test universal properties across input spaces
- **End-to-End Tests**: Test complete user workflows

**Quality Assurance**:
- Automated test execution in CI/CD pipeline
- Comprehensive error handling validation
- Performance and load testing
- Data quality and validation testing

---

## Test Architecture

### Test Categories

```
┌─────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                          │
│                                                             │
│                    ┌─────────────┐                         │
│                    │     E2E     │ 5% - Full workflows     │
│                    │    Tests    │                         │
│                    └─────────────┘                         │
│                 ┌─────────────────────┐                    │
│                 │  Integration Tests  │ 15% - Components   │
│                 │                     │                    │
│                 └─────────────────────┘                    │
│            ┌─────────────────────────────────┐             │
│            │        Unit Tests               │ 60% - Units │
│            │                                 │             │
│            └─────────────────────────────────┘             │
│       ┌─────────────────────────────────────────────┐      │
│       │           Property-Based Tests              │ 20%  │
│       │        (Cross-cutting validation)           │      │
│       └─────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Test Statistics

| Test Type | Count | Coverage | Purpose |
|-----------|-------|----------|---------|
| **Unit Tests** | 60+ | Individual functions | Component isolation |
| **Integration Tests** | 25+ | Component interaction | Workflow validation |
| **Property Tests** | 69+ | Universal properties | Correctness guarantees |
| **E2E Tests** | 10+ | Full system | User experience |
| **Performance Tests** | 15+ | System performance | Load validation |

**Total**: 180+ tests with 80%+ code coverage

---

## Unit Testing

### Test Structure

**Standard Test Pattern**:
```python
import pytest
from unittest.mock import Mock, patch
from app.services.pipeline.component import Component

class TestComponent:
    """Test suite for Component class"""
    
    def test_component_basic_functionality(self):
        """Test basic component operation"""
        # Arrange
        component = Component()
        input_data = {"key": "value"}
        
        # Act
        result = component.process(input_data)
        
        # Assert
        assert result is not None
        assert result["status"] == "success"
    
    def test_component_error_handling(self):
        """Test component handles errors gracefully"""
        component = Component()
        
        with pytest.raises(ValueError):
            component.process(None)
    
    @patch('app.services.external_api')
    def test_component_with_mocking(self, mock_api):
        """Test component with external dependencies mocked"""
        mock_api.fetch_data.return_value = {"data": "test"}
        
        component = Component()
        result = component.process_external()
        
        assert result["data"] == "test"
        mock_api.fetch_data.assert_called_once()
```

### Key Unit Test Areas

#### 1. Data Pipeline Components
**Location**: `tests/test_pipeline/`

**Coverage**:
- Ingestion modules (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
- Processing modules (data cleaning, validation, transformation)
- Merge functionality (temporal and spatial alignment)

**Example**:
```python
def test_chirps_ingestion_valid_data():
    """Test CHIRPS ingestion with valid parameters"""
    ingester = ChirpsIngestion()
    result = ingester.fetch_data(
        start_date="2023-01-01",
        end_date="2023-01-31",
        location=(-6.8, 39.3)
    )
    
    assert len(result) == 31  # Daily data for January
    assert all(col in result.columns for col in ['date', 'rainfall'])
    assert result['rainfall'].dtype == 'float64'
```

#### 2. ML Model Components
**Location**: `tests/test_models/`

**Coverage**:
- Model training and prediction
- Feature engineering pipeline
- Model evaluation metrics
- Uncertainty quantification

**Example**:
```python
def test_random_forest_training():
    """Test Random Forest model training"""
    X_train, y_train = generate_sample_data()
    
    model = RandomForestModel()
    model.train(X_train, y_train)
    
    assert model.is_trained
    assert model.feature_importance_ is not None
    assert len(model.feature_importance_) == X_train.shape[1]
```

#### 3. API Endpoints
**Location**: `tests/test_api/`

**Coverage**:
- Authentication endpoints
- Dashboard data endpoints
- Model prediction endpoints
- Administrative endpoints

**Example**:
```python
def test_dashboard_kpis_endpoint(client, auth_headers):
    """Test dashboard KPIs endpoint"""
    response = client.get("/api/dashboard/kpis", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "trigger_rates" in data
    assert "loss_ratio" in data
    assert "sustainability_status" in data
```

---

## Integration Testing

### Test Scenarios

#### 1. End-to-End Pipeline
**Location**: `tests/test_integration/test_pipeline_integration.py`

**Scenarios**:
- Complete data ingestion → processing → merging workflow
- Multi-source data integration
- Error handling across pipeline stages
- Performance under load

**Example**:
```python
@pytest.mark.integration
async def test_complete_pipeline_execution():
    """Test complete pipeline from ingestion to output"""
    # Arrange
    pipeline = PipelineOrchestrator()
    
    # Act
    result = await pipeline.execute_full_pipeline(
        sources=['chirps', 'nasa_power'],
        date_range=('2023-01-01', '2023-01-31')
    )
    
    # Assert
    assert result.status == 'completed'
    assert result.records_processed > 0
    assert result.sources_succeeded == ['chirps', 'nasa_power']
    
    # Verify output files exist
    assert os.path.exists('outputs/processed/master_dataset.csv')
```

#### 2. Model Training Integration
**Location**: `tests/test_integration/test_model_integration.py`

**Scenarios**:
- Data preprocessing → feature engineering → model training
- Multi-model ensemble creation
- Model evaluation and validation
- Model persistence and loading

#### 3. API Integration
**Location**: `tests/test_integration/test_api_integration.py`

**Scenarios**:
- Authentication flow
- Dashboard data retrieval
- Real-time prediction requests
- Error handling and rate limiting

### Integration Test Configuration

**Test Database**:
```python
@pytest.fixture(scope="session")
def test_db():
    """Create test database for integration tests"""
    engine = create_engine("postgresql://test:test@localhost/climate_test")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

**Test Data**:
```python
@pytest.fixture
def sample_climate_data():
    """Generate sample climate data for testing"""
    return pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'temperature': np.random.normal(25, 5, 100),
        'rainfall': np.random.exponential(2, 100),
        'location': 'test_location'
    })
```

---

## Property-Based Testing

### Hypothesis Framework

**Property-based testing** uses the Hypothesis library to automatically generate test cases and discover edge cases:

```python
from hypothesis import given, strategies as st
from hypothesis.extra.pandas import data_frames, column

@given(data_frames([
    column('temperature', dtype=float, elements=st.floats(-50, 60)),
    column('rainfall', dtype=float, elements=st.floats(0, 500)),
]))
def test_climate_processing_properties(df):
    """Test climate processing maintains data properties"""
    processor = ClimateProcessor()
    result = processor.process(df)
    
    # Property: Output has same number of rows
    assert len(result) == len(df)
    
    # Property: No negative rainfall after processing
    assert all(result['rainfall'] >= 0)
    
    # Property: Temperature within reasonable bounds
    assert all(-60 <= result['temperature'] <= 70)
```

### Key Properties Tested

#### 1. Data Pipeline Properties
**Location**: `tests/test_properties/test_pipeline_properties.py`

**Properties**:
- Data completeness preservation
- Temporal ordering maintenance
- No data leakage between train/test splits
- Consistent data types after processing

#### 2. Model Properties
**Location**: `tests/test_properties/test_model_properties.py`

**Properties**:
- Prediction consistency (same input → same output)
- Uncertainty bounds validity (lower ≤ prediction ≤ upper)
- Feature importance non-negativity
- Model performance bounds

#### 3. API Properties
**Location**: `tests/test_properties/test_api_properties.py`

**Properties**:
- Response format consistency
- Authentication token validity
- Rate limiting enforcement
- Error message structure

### Property Test Examples

#### Data Validation Properties
```python
@given(st.lists(st.floats(), min_size=1, max_size=1000))
def test_data_quality_metrics_properties(data):
    """Test data quality metrics maintain mathematical properties"""
    metrics = calculate_quality_metrics(data)
    
    # Property: Completeness is between 0 and 1
    assert 0 <= metrics['completeness'] <= 1
    
    # Property: Quality score is between 0 and 100
    assert 0 <= metrics['quality_score'] <= 100
    
    # Property: Outlier percentage is between 0 and 100
    assert 0 <= metrics['outlier_percentage'] <= 100
```

#### Model Prediction Properties
```python
@given(st.lists(st.lists(st.floats(-10, 10), min_size=74, max_size=74), 
               min_size=1, max_size=100))
def test_ensemble_prediction_properties(feature_matrix):
    """Test ensemble predictions maintain consistency properties"""
    model = EnsembleModel.load('outputs/models/')
    predictions = model.predict(np.array(feature_matrix))
    
    # Property: Predictions are finite numbers
    assert all(np.isfinite(predictions))
    
    # Property: Prediction intervals are ordered
    lower, pred, upper = model.predict_with_uncertainty(np.array(feature_matrix))
    assert all(lower <= pred)
    assert all(pred <= upper)
```

---

## Performance Testing

### Load Testing

**Location**: `tests/test_performance/`

**Scenarios**:
- High-volume data ingestion
- Concurrent API requests
- Large dataset processing
- Memory usage under load

**Example**:
```python
import time
import concurrent.futures

def test_api_performance_under_load():
    """Test API performance with concurrent requests"""
    def make_request():
        response = client.get("/api/dashboard/kpis")
        return response.status_code, response.elapsed.total_seconds()
    
    # Test with 50 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [future.result() for future in futures]
    
    # Assert all requests succeeded
    assert all(status == 200 for status, _ in results)
    
    # Assert 95th percentile response time < 500ms
    response_times = [duration for _, duration in results]
    p95_time = np.percentile(response_times, 95)
    assert p95_time < 0.5
```

### Memory Testing

```python
import psutil
import os

def test_memory_usage_during_processing():
    """Test memory usage stays within bounds during processing"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Process large dataset
    large_dataset = generate_large_climate_dataset(10000)  # 10k records
    processor = ClimateProcessor()
    result = processor.process(large_dataset)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Assert memory increase < 500MB
    assert memory_increase < 500
```

---

## Test Execution

### Running Tests

#### All Tests
```bash
# Run complete test suite
cd backend
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

#### Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/test_unit/ -v

# Integration tests only
python -m pytest tests/test_integration/ -v

# Property-based tests only
python -m pytest tests/test_properties/ -v

# Performance tests only
python -m pytest tests/test_performance/ -v
```

#### Specific Test Files
```bash
# Single test file
python -m pytest tests/test_models/test_ensemble.py -v

# Single test function
python -m pytest tests/test_api/test_dashboard.py::test_kpis_endpoint -v

# Tests matching pattern
python -m pytest -k "test_prediction" -v
```

### Test Configuration

**pytest.ini**:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    property: Property-based tests
    performance: Performance tests
    slow: Slow-running tests
```

**conftest.py**:
```python
import pytest
import asyncio
from sqlalchemy import create_engine
from app.database import Base
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Test database fixture"""
    engine = create_engine("postgresql://test:test@localhost/climate_test")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    """Test client fixture"""
    from fastapi.testclient import TestClient
    return TestClient(app)
```

---

## Continuous Integration

### GitHub Actions Workflow

**Location**: `.github/workflows/tests.yml`

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
          POSTGRES_PASSWORD: test
          POSTGRES_DB: climate_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio hypothesis pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

### Test Quality Gates

**Coverage Requirements**:
- Overall coverage: ≥80%
- New code coverage: ≥90%
- Critical components: ≥95%

**Performance Requirements**:
- Unit tests: <10s total
- Integration tests: <60s total
- API response time: <500ms (95th percentile)
- Memory usage: <2GB peak

---

## Test Data Management

### Test Data Generation

**Synthetic Data**:
```python
def generate_climate_test_data(n_samples=100, n_locations=3):
    """Generate synthetic climate data for testing"""
    np.random.seed(42)  # Reproducible
    
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='D')
    locations = [f'location_{i}' for i in range(n_locations)]
    
    data = []
    for location in locations:
        for date in dates:
            data.append({
                'date': date,
                'location': location,
                'temperature': np.random.normal(25, 5),
                'rainfall': np.random.exponential(2),
                'humidity': np.random.uniform(30, 90),
                'ndvi': np.random.uniform(0.1, 0.9)
            })
    
    return pd.DataFrame(data)
```

**Test Data Fixtures**:
```python
@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        'temperature': [20.5, 22.1, 19.8, 21.3],
        'rainfall': [0.0, 5.2, 12.1, 0.5],
        'humidity': [65, 70, 85, 60],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
    }

@pytest.fixture
def trained_model():
    """Pre-trained model for testing"""
    model = RandomForestModel()
    X, y = generate_sample_data()
    model.train(X, y)
    return model
```

### Test Database Management

**Database Isolation**:
```python
@pytest.fixture(autouse=True)
def clean_database(test_db):
    """Clean database before each test"""
    # Truncate all tables
    for table in reversed(Base.metadata.sorted_tables):
        test_db.execute(table.delete())
    test_db.commit()
```

---

## Debugging and Troubleshooting

### Common Test Issues

#### 1. Database Connection Errors
**Error**: `could not connect to server`  
**Solution**:
```bash
# Start test database
docker-compose up -d db

# Verify connection
psql postgresql://test:test@localhost/climate_test -c "SELECT 1"
```

#### 2. Import Path Issues
**Error**: `ModuleNotFoundError: No module named 'app'`  
**Solution**:
```bash
# Set PYTHONPATH
export PYTHONPATH=$PWD/backend:$PYTHONPATH

# Or run from backend directory
cd backend && python -m pytest tests/
```

#### 3. Async Test Issues
**Error**: `RuntimeError: Event loop is closed`  
**Solution**:
```python
# Ensure proper async fixture
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Use async marker
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

#### 4. Property Test Failures
**Error**: `hypothesis.errors.Flaky`  
**Solution**:
```python
# Add explicit seed for reproducibility
@given(st.integers())
@settings(max_examples=100, deadline=None)
def test_with_settings(value):
    # Test implementation
    pass
```

### Test Debugging Tools

**Verbose Output**:
```bash
# Show detailed test output
python -m pytest tests/ -vv -s

# Show print statements
python -m pytest tests/ -s

# Stop on first failure
python -m pytest tests/ -x
```

**Coverage Analysis**:
```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Show missing lines
python -m pytest tests/ --cov=app --cov-report=term-missing
```

**Performance Profiling**:
```bash
# Profile test execution
python -m pytest tests/ --profile

# Memory profiling
python -m pytest tests/ --memprof
```

---

## Test Maintenance

### Adding New Tests

**Checklist**:
- [ ] Choose appropriate test type (unit/integration/property)
- [ ] Follow naming conventions (`test_*.py`, `test_*()`)
- [ ] Add appropriate markers (`@pytest.mark.unit`)
- [ ] Include docstrings explaining test purpose
- [ ] Use appropriate fixtures for setup/teardown
- [ ] Verify test passes and fails appropriately
- [ ] Update test documentation

**Example New Test**:
```python
@pytest.mark.unit
def test_new_feature_basic_functionality():
    """Test that new feature works with valid input"""
    # Arrange
    feature = NewFeature()
    valid_input = {"param": "value"}
    
    # Act
    result = feature.process(valid_input)
    
    # Assert
    assert result["status"] == "success"
    assert "output" in result
```

### Updating Existing Tests

**When to Update**:
- Code behavior changes
- New edge cases discovered
- Performance requirements change
- API contracts change

**Update Process**:
1. Identify affected tests
2. Update test expectations
3. Run tests to verify changes
4. Update test documentation
5. Review with team

### Test Refactoring

**Common Refactoring Patterns**:
- Extract common setup into fixtures
- Parameterize similar tests
- Split large test files
- Consolidate duplicate assertions

**Example Refactoring**:
```python
# Before: Duplicate setup
def test_feature_case_1():
    feature = Feature()
    feature.configure({"setting": "value"})
    result = feature.process("input1")
    assert result == "expected1"

def test_feature_case_2():
    feature = Feature()
    feature.configure({"setting": "value"})
    result = feature.process("input2")
    assert result == "expected2"

# After: Parameterized test
@pytest.mark.parametrize("input_val,expected", [
    ("input1", "expected1"),
    ("input2", "expected2"),
])
def test_feature_cases(configured_feature, input_val, expected):
    result = configured_feature.process(input_val)
    assert result == expected

@pytest.fixture
def configured_feature():
    feature = Feature()
    feature.configure({"setting": "value"})
    return feature
```

---

## Recent Test Fixes and Improvements

### January 2026 - Data Pipeline Test Fixes (Tasks 11-17)

**Status**: ✅ Complete  
**Details**: [DATA_PIPELINE_TEST_FIXES.md](../reports/DATA_PIPELINE_TEST_FIXES.md)

Resolved 10 critical test failures in the data pipeline:

**Issues Fixed**:
1. ✅ Missing year/month columns in merge operations
2. ✅ Empty validation sets in temporal splitting
3. ✅ Flood trigger logic not activating
4. ✅ Empty dataframes in preprocessing pipeline
5. ✅ 1,872 duplicate year-month records
6. ✅ Pipeline dry run test failures

**Key Improvements**:
- **Temporal Column Handling**: All processing modules now consistently include year/month columns
- **NaN Handling Strategy**: Improved to preserve more samples while maintaining data quality
- **Edge Case Handling**: Better handling of small datasets in temporal splitting
- **Deduplication Logic**: Proper merge operations prevent duplicate records
- **Validation**: Added comprehensive validation at each pipeline stage

**Test Results**:
- Before: 35/45 tests passing (10 failures)
- After: 45/45 tests passing (100% pass rate)
- Coverage: 80%+ maintained

**Technical Details**:
- Updated 5 processing modules for consistent temporal columns
- Improved preprocessing NaN handling to preserve samples
- Fixed temporal splitting edge cases for small datasets
- Implemented proper deduplication in merge operations
- Added validation checks at each pipeline stage

### December 2025 - CI/CD Pipeline Fixes (Tasks 1-10)

**Status**: ✅ Complete  
**Details**: [CI_CD_FIX.md](../reports/CI_CD_FIX.md)

Fixed CI/CD pipeline failures and code quality issues:

**Issues Fixed**:
1. ✅ Import errors and missing dependencies
2. ✅ Code formatting and style issues
3. ✅ Linting configuration
4. ✅ Test collection errors

**Key Improvements**:
- Added backward compatibility wrapper for pipeline imports
- Configured black, isort, and flake8 for consistent code style
- Fixed import errors preventing test collection
- Removed deprecated code and cleaned up architecture

**Test Results**:
- All tests now collect successfully
- CI/CD pipeline passes on Python 3.9, 3.10, 3.11
- Appropriate test skipping for optional dependencies

---

## Related Documentation

- **[DATA_PIPELINE_REFERENCE.md](./DATA_PIPELINE_REFERENCE.md)** - Pipeline testing details
- **[ML_MODEL_REFERENCE.md](./ML_MODEL_REFERENCE.md)** - Model testing approaches
- **[DEPLOYMENT_REFERENCE.md](./DEPLOYMENT_REFERENCE.md)** - Production testing
- **[API_REFERENCE.md](./API_REFERENCE.md)** - API testing documentation

---

**Document Version**: 2.0  
**Last Updated**: January 4, 2026  
**Status**: ✅ Production Ready  
**Consolidates**: ALL_TESTS_COMPLETE.md, TESTING_INSTRUCTIONS.md, TEST_STATUS_FINAL.md, TEST_IMPLEMENTATION_COMPLETE.md, TEST_CHECKPOINT_REPORT.md, INTEGRATION_TESTS_SUMMARY.md, TEMPORAL_LEAKAGE_FIX.md