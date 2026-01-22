# Testing Infrastructure - Complete Reference

**Last Updated**: January 22, 2026  
**Status**: Production Ready

---

## Overview

Comprehensive testing and monitoring infrastructure for the climate prediction pipeline, including mock APIs for all external data sources, integration tests, and automated monitoring.

## 🧪 Integration Testing with Mock APIs

### Available Mock APIs

All 5 external data sources have mock implementations:

1. **CHIRPS** (`mock_chirps.py`) - Rainfall data via Google Earth Engine
2. **NASA POWER** (`mock_nasa_power.py`) - Temperature, humidity, solar radiation
3. **ERA5** (`mock_era5.py`) - Reanalysis data via Copernicus CDS
4. **NDVI** (`mock_ndvi.py`) - Vegetation index via Google Earth Engine
5. **Ocean Indices** (`mock_ocean_indices.py`) - ENSO ONI and IOD

### Test Suite Coverage

**Integration Tests** (`test_ingestion_with_mocks.py`):
- ✅ 25+ tests covering all data sources
- ✅ Mock unit tests (basic functionality)
- ✅ Error simulation tests
- ✅ Performance validation (< 1s for 5 years)
- ✅ Edge case handling
- ✅ Full pipeline integration tests

**ML Model Tests** (`README_ML_TESTS.md`):
- ✅ 21 preprocessing tests
- ✅ 15 model training tests  
- ✅ 17 evaluation tests
- ✅ End-to-end pipeline tests

**Data Pipeline Tests**:
- ✅ Ingestion module tests
- ✅ Processing module tests
- ✅ Merge functionality tests
- ✅ Validation tests

### Running Tests

```bash
# All integration tests with mocks
pytest tests/test_ingestion_with_mocks.py -v

# Specific mock test
pytest tests/test_ingestion_with_mocks.py::test_mock_chirps_basic -v

# All ML tests
pytest tests/test_*.py -v

# With coverage
pytest --cov=modules --cov=models --cov=utils -v
```

### Mock API Benefits

| Aspect | Real APIs | Mock APIs |
|--------|-----------|-----------|
| **Speed** | Minutes | < 1 second |
| **Reliability** | Network dependent | 100% reliable |
| **Cost** | API usage charges | Free |
| **Offline** | Requires internet | Works offline |
| **Reproducibility** | Variable | Deterministic |
| **Error Testing** | Limited control | Full control |

## 📊 Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| **Mock APIs** | 25+ | ✅ Complete |
| **Preprocessing** | 21 | ✅ Complete |
| **Models** | 15 | ✅ Complete |
| **Evaluation** | 17 | ✅ Complete |
| **Data Pipeline** | 45+ | ✅ Complete |
| **Total** | 120+ | ✅ 80%+ coverage |

## 🔍 What Gets Tested

### Data Ingestion (with Mocks)
- ✅ All 5 data source integrations
- ✅ API response parsing
- ✅ Error handling and retries
- ✅ Data format validation
- ✅ Multi-location support (CHIRPS)

### Data Processing
- ✅ Domain-specific transformations
- ✅ Trigger calculations (drought, flood)
- ✅ Data quality checks
- ✅ Missing value handling
- ✅ Temporal consistency

### Feature Engineering
- ✅ Lag features (1, 3, 6, 12 months)
- ✅ Rolling statistics
- ✅ Interaction features
- ✅ Normalization
- ✅ Temporal splitting

### Model Training
- ✅ Random Forest
- ✅ XGBoost
- ✅ LSTM
- ✅ Ensemble
- ✅ Save/load functionality

### Model Evaluation
- ✅ Metrics (R², RMSE, MAE, MAPE)
- ✅ Uncertainty quantification
- ✅ Seasonal performance
- ✅ Feature importance

## 🚀 For Automated Forecasting Pipeline

**The testing infrastructure is ideal for your automated forecasting pipeline:**

### Before Each Run
```bash
# Validate environment
python scripts/dev_dashboard_summary.py

# Check data quality
python scripts/validate_data_quality.py
```

### During Development
```bash
# Test with mocks (fast iteration)
pytest tests/test_ingestion_with_mocks.py -v

# Test full pipeline
pytest -v
```

### After Deployment
```bash
# Monitor health
python scripts/monitor_pipeline_health.py --send-alerts

# Get Slack notifications automatically
# (configured in .env)
```

## 📈 Continuous Integration

**Recommended CI/CD workflow:**

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run mock integration tests
        run: pytest tests/test_ingestion_with_mocks.py -v
      - name: Run all tests
        run: pytest --cov=modules --cov=models --cov=utils -v
      - name: Upload coverage
        run: codecov
```

## 🎯 Testing Best Practices

### Development Workflow

1. **Write tests first** (TDD approach)
2. **Use mocks for external APIs** (fast, reliable)
3. **Test error scenarios** (use mock error simulation)
4. **Validate with real APIs** (before production)
5. **Monitor in production** (use health checks)

### Test Organization

```
tests/
├── mocks/                      # Mock API implementations
│   ├── README.md              # Usage guide
│   └── mock_*.py              # Individual mocks
├── test_ingestion_with_mocks.py  # Integration tests
├── test_preprocessing.py       # ML preprocessing
├── test_models.py             # Model training
├── test_evaluation.py         # Model evaluation
└── test_*.py                  # Other test suites
```

### When to Use Mocks vs Real APIs

**Use Mocks:**
- ✅ Unit and integration tests
- ✅ CI/CD pipelines
- ✅ Local development
- ✅ Error scenario testing
- ✅ Performance testing

**Use Real APIs:**
- ✅ Final validation before deployment
- ✅ Verifying API contract changes
- ✅ Production data collection
- ✅ End-to-end smoke tests

## 📚 Related Documentation

- **[Mock API Usage Guide](../tests/mocks/README.md)** - Detailed mock API documentation
- **[ML Testing Guide](README_ML_TESTS.md)** - ML model testing details  
- **[Dev Deployment](../docs/DEV_DEPLOYMENT.md)** - Development setup
- **[Monitoring Guide](../docs/MONITORING_GUIDE.md)** - Health checks and alerts

---

**Maintained by**: Tanzania Climate Prediction Team  
**For Questions**: See main project README
