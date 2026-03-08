# Tanzania Climate Prediction - Phase 2

> **Status**: 🔵 Shadow Run ACTIVE (Mar 7 – Jun 5, 2026) · Live at [hewasense.majaribio.com](https://hewasense.majaribio.com)

A comprehensive end-to-end machine learning system for climate prediction in Tanzania, featuring data ingestion, processing, feature engineering, model training pipelines, and an **interactive web dashboard** supporting parametric insurance for smallholder farmers.

**Current Pilot**: 1,000 rice farmers in the Kilombero Basin (Morogoro, Tanzania). The system is generating daily forecasts and accumulating Brier Score evidence for underwriter engagement.

## 🎉 Interactive Dashboard System

**Production-ready web application for climate insights and risk management — live on server!**

👉 **Live**: [https://hewasense.majaribio.com](https://hewasense.majaribio.com)
👉 **Local Setup**: [GETTING_STARTED.md](docs/guides/GETTING_STARTED.md) - 5-minute setup with Docker

**7 Dashboard Views**:
- 📊 Executive Dashboard - Business KPIs, loss ratios, portfolio metrics
- 🤖 Model Performance Monitoring - ML accuracy tracking, drift detection
- ⚡ Triggers Dashboard - Insurance trigger events and alerts
- 🌍 Climate Insights - 25-year historical time series (2000–2026, 6 locations)
- 📈 Risk Management - Historical backtesting validation (phase-based parametric model)
- 🔔 Early Warning - Forward forecast alerts (fires on threshold breaches)
- 🗂️ Evidence Pack - Shadow run Brier Score accumulation for underwriters

**Quick Start**:
```bash
# Local development (use docker-compose.dev.yml)
docker compose -f docker-compose.dev.yml up -d
# Access at http://localhost:3000
```

> **Note**: This project uses `docker-compose.dev.yml` for local development and the server uses `docker compose` (v2 plugin, not the legacy `docker-compose` with hyphen). See [GETTING_STARTED.md](docs/guides/GETTING_STARTED.md) for full setup instructions.

See **[docs/current/EXECUTIVE_SUMMARY.md](docs/current/EXECUTIVE_SUMMARY.md)** for the latest project status and performance metrics.

---

## Overview

Phase 2 delivers a complete ML system that:
- **Data Pipeline**: Ingests climate data from 5 major sources (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
- **Processing**: Validates and processes data with comprehensive error handling and domain-specific features
- **Feature Engineering**: Creates ML-ready features with lag, rolling statistics, and interactions
- **Model Training**: Trains multiple models (Random Forest, XGBoost, LSTM, Ensemble) with experiment tracking
- **Evaluation**: Provides comprehensive model evaluation with uncertainty quantification
- **Testing**: Includes 180+ tests ensuring data quality and model reliability
- **🆕 Interactive Dashboard**: Web-based visualization and monitoring system

## Project Structure

```
phase2/
├── modules/
│   ├── ingestion/              # Data fetching from 5 sources
│   │   ├── nasa_power_ingestion.py
│   │   ├── era5_ingestion.py
│   │   ├── chirps_ingestion.py
│   │   ├── ndvi_ingestion.py
│   │   └── ocean_indices_ingestion.py
│   ├── processing/             # Domain-specific processing
│   │   ├── process_nasa_power.py
│   │   ├── process_era5.py
│   │   ├── process_chirps.py    # Drought/flood triggers
│   │   ├── process_ndvi.py
│   │   ├── process_ocean_indices.py
│   │   └── merge_processed.py   # Merge all sources
│   └── reporting/
│       └── output_reporting.py
│
├── preprocessing/              # ML feature engineering
│   └── preprocess.py          # Lag, rolling, interactions, normalization
│
├── pipelines/                  # Pipeline orchestration
│   ├── run_data_pipeline.py   # Data ingestion & processing
│   ├── quick_model_pipeline.py # Fast prototyping (~2-5 min)
│   ├── model_development_pipeline.py # Full ML pipeline (spec-compliant)
│   └── README.md              # Pipeline documentation
│
├── train_pipeline.py          # Enhanced ML training pipeline (RECOMMENDED)
├── train_pipeline_old_deprecated.py # Old version (DO NOT USE)
│
├── models/                     # Model implementations
│   ├── random_forest_model.py
│   ├── xgboost_model.py
│   ├── lstm_model.py
│   ├── ensemble_model.py
│   ├── train_models.py        # Training orchestration
│   ├── evaluation.py          # Evaluation engine
│   ├── experiment_tracking.py # Experiment logging
│   └── model_config.py        # Hyperparameters
│
├── evaluation/                 # Evaluation utilities
│   └── evaluate.py
│
├── utils/                      # Shared utilities
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging utilities
│   ├── validator.py           # Data validation
│   ├── validation.py          # Additional validators
│   ├── cache.py               # Caching utilities
│   ├── versioning.py          # Data versioning
│   └── performance.py         # Performance monitoring
│
├── tests/                      # 45+ comprehensive tests
│   ├── test_pipeline.py
│   ├── test_merge_processed.py
│   ├── test_chirps_processing.py
│   ├── test_earth_engine_setup.py
│   ├── test_cache.py
│   ├── test_versioning.py
│   └── ...
│
├── docs/                       # Documentation
│   ├── README.md
│   ├── DEV_DEPLOYMENT.md        #  🆕 Dev environment setup guide
│   ├── MONITORING_GUIDE.md      # 🆕 Monitoring & alerting guide
│   ├── TESTING_MONITORING_REFERENCE.md  # 🆕 Quick reference
│   ├── MODEL_DEVELOPMENT_GUIDE.md
│   ├── BUSINESS_REPORTS_GUIDE.md
│   ├── pipeline_overview.md
│   └── IMPLEMENTATION_STATUS.md

├── tests/                      # Comprehensive testing
│   ├── mocks/                  # 🆕 Mock APIs for integration testing
│   │   ├── mock_base.py        # Base classes and data generators
│   │   ├── mock_chirps.py      # CHIRPS rainfall mock
│   │   ├── mock_nasa_power.py  # NASA POWER climate mock
│   │   ├── mock_era5.py        # ERA5 reanalysis mock
│   │   ├── mock_ndvi.py        # NDVI vegetation mock
│   │   ├── mock_ocean_indices.py  # Ocean indices mock
│   │   └── README.md           # Mock API usage guide
│   ├── test_ingestion_with_mocks.py  # 🆕 Integration tests with mocks
│   ├── test_pipeline.py
│   ├── test_merge_processed.py
│   ├── test_chirps_processing.py
│   └── ...
├── scripts/                    # Utility scripts
│   ├── monitor_pipeline_health.py  # 🆕 Pipeline health monitoring
│   ├── validate_data_quality.py    # 🆕 Data quality validation
│   ├── dev_dashboard_summary.py    # 🆕 Dev environment dashboard
│   ├── analysis/              # EDA and visualization scripts
│   ├── demos/                 # Demo scripts for testing
│   ├── reporting/             # Business report generation
│   │   └── generate_business_reports.py
│   └── verification/          # Testing and verification utilities
│
├── utils/                      # Shared utilities
│   ├── slack_notifier.py      # 🆕 Slack alerting integration
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging utilities
│   ├── validator.py           # Data validation
│   ├── validation.py          # Additional validators
│   ├── cache.py               # Caching utilities
│   ├── versioning.py          # Data versioning
│   └── performance.py         # Performance monitoring
```

## Data Sources

### 1. NASA POWER
- **Source**: NASA Prediction of Worldwide Energy Resources
- **Data**: Temperature, solar radiation
- **API**: https://power.larc.nasa.gov/api/temporal/monthly/point

### 2. ERA5
- **Source**: ECMWF Reanalysis v5
- **Data**: Temperature, humidity, atmospheric variables
- **Access**: Requires API key

### 3. CHIRPS
- **Source**: Climate Hazards Group InfraRed Precipitation with Station data
- **Data**: Rainfall measurements
- **URL**: https://data.chc.ucsb.edu/products/CHIRPS-2.0

### 4. NDVI
- **Source**: Normalized Difference Vegetation Index
- **Data**: Vegetation health indicators
- **Format**: Satellite imagery data

### 5. Ocean Indices
- **Source**: NOAA Climate Indices
- **Data**: ENSO, IOD (Indian Ocean Dipole)
- **URL**: https://psl.noaa.gov/data/climateindices/list/

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/lordwalt/climate_prediction_TZ.git
cd climate_prediction_TZ/phase2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

## Usage

### 1. Data Pipeline

**Dry-run mode (with mock data):**
```bash
python run_pipeline.py --debug
```

**Production mode (fetch real data):**
```bash
python run_pipeline.py
```

**Custom date range:**
```bash
python pipelines/run_data_pipeline.py --start-year 2010 --end-year 2020
```

### 2. Model Training

**Enhanced Training Pipeline (RECOMMENDED):**
```bash
# Full pipeline with feature selection, baselines, and validation
python train_pipeline.py

# Skip feature selection (not recommended)
python train_pipeline.py --skip-feature-selection

# Custom feature count (default: 75, actual selected: 77 after source diversity)
python train_pipeline.py --target-features 75

# Skip preprocessing if features exist
python train_pipeline.py --skip-preprocessing
```

**Quick prototyping (fast, no preprocessing):**
```bash
python pipelines/quick_model_pipeline.py
```

**Legacy ML pipeline (alternative):**
```bash
# Train all models
python model_development_pipeline.py

# Train specific models
python model_development_pipeline.py --models rf,xgb

# Named experiment
python model_development_pipeline.py --experiment-name rainfall_v2
```

**Note**: `train_pipeline.py` includes scientifically sound improvements:
- Feature selection (594 → 77 features, Feb 2026 retraining)
- Baseline model comparison
- Enhanced regularization
- Automated validation checks

See `docs/MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md` for details.

### 3. Business Reports

**Generate all business metrics reports:**
```bash
python scripts/reporting/generate_business_reports.py
```

**With custom data source:**
```bash
python scripts/reporting/generate_business_reports.py --data path/to/data.csv
```

**Outputs** (saved to `outputs/business_reports/`):
- Executive summary with key metrics
- Insurance trigger events timeline
- Drought/flood/crop failure alerts
- Financial impact analysis and payout estimates
- Risk assessment dashboard
- Visualizations (charts and heatmaps)

See `docs/BUSINESS_REPORTS_GUIDE.md` for detailed documentation.

### 4. Running Tests

**Run all tests:**
```bash
pytest -v
```

**Run specific test suite:**
```bash
pytest tests/test_pipeline.py -v
pytest tests/test_merge_processed.py -v
pytest tests/test_chirps_processing.py -v
```

**Run with coverage:**
```bash
pytest --cov=modules --cov=utils --cov=models --cov=preprocessing -v
```

### 🆕 Integration Testing with Mock APIs

**Fast, reliable testing without network calls:**
```bash
# Run all mock integration tests (100x faster than real APIs)
pytest tests/test_ingestion_with_mocks.py -v

# Test specific data source mock
pytest tests/test_ingestion_with_mocks.py::test_mock_chirps_basic -v

# Test full pipeline with all mocks
pytest tests/test_ingestion_with_mocks.py::test_full_pipeline_with_mocks -v
```

**Benefits:**
- ✅ No external API dependencies
- ✅ Deterministic test results  
- ✅ < 1 second execution time
- ✅ Test error scenarios easily
- ✅ Works offline

See [tests/mocks/README.md](tests/mocks/README.md) for mock API usage guide.

### 🆕 Development Monitoring & Health Checks

**Monitor pipeline health:**
```bash
# Check data freshness and completeness
python scripts/monitor_pipeline_health.py

# With Slack alerts
python scripts/monitor_pipeline_health.py --send-alerts

# Validate data quality
python scripts/validate_data_quality.py --source CHIRPS

# View dev environment dashboard
python scripts/dev_dashboard_summary.py
```

**Slack Integration (Automated Alerts):**
- ✅ Pipeline status notifications
- ✅ Error alerts with stack traces
- ✅ Data quality warnings
- ✅ Real-time monitoring

See [docs/DEV_DEPLOYMENT.md](docs/DEV_DEPLOYMENT.md) and [docs/MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md) for complete guides.

**Perfect for Automated Forecasting Pipeline:**
- Monitor scheduled pipeline runs automatically
- Get instant Slack alerts for failures
- Validate forecast data quality
- Track pipeline performance over time

## Configuration

### Environment Variables

Create a `.env` file based on `.env.template`:

```env
# NASA POWER API
NASA_API_URL=https://power.larc.nasa.gov/api/temporal/monthly/point

# ERA5 API
ERA5_API_KEY=your_api_key_here

# CHIRPS Data
CHIRPS_BASE_URL=https://data.chc.ucsb.edu/products/CHIRPS-2.0

# NDVI Source
NDVI_SOURCE=your_ndvi_source

# Ocean Indices
OCEAN_INDICES_SOURCE=https://psl.noaa.gov/data/climateindices/list/

# Project Settings
DEFAULT_REGION=Tanzania
DEFAULT_CRS=EPSG:4326

# 🆕 Development & Monitoring Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/climate_dev
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
RETRY_MAX_ATTEMPTS=3
DATA_STALENESS_THRESHOLD_DAYS=7
MONITORING_METRICS_PORT=9090
```

**New in March 2026:**
- **Shadow Run ACTIVE**: Daily 6AM EAT pipeline generating 12 forecasts/day, accumulating Brier Scores
- **Evidence Pack Dashboard**: Tracks forecast accuracy over time for underwriter engagement
- **Historical Backtesting**: Phase-based parametric model (GDD-tracked, 4 growth phases) validated on 2015-2025 data — 3/8 documented events matched
- **Automated Evaluation**: ForecastLog records auto-resolve when validity windows mature (~Jun 2026 first Brier Scores)

**New in February 2026:**
- **Actuarial Refinement (HewaSense V4)**: GDD integration, cumulative flood triggers, out-of-sample validation (2000-2014)
- **6-Location Phase-Based Backtesting**: Dual-index triggers, phase-weighted payouts, 22.6% loss ratio (sustainable)
- **Early Warning Dashboard**: Real-time forward alert view (displays when threshold breaches detected)

**New in January 2026:**
- **Mock APIs**: Test all data sources without network calls
- **Slack Alerts**: Real-time notifications for pipeline status
- **Monitoring Scripts**: Health checks and quality validation
- **Retry Configuration**: Best practices documented (3 for dev, 5-7 for production)

See [docs/DEV_DEPLOYMENT.md](docs/DEV_DEPLOYMENT.md) for complete setup guide.

## Pipeline Workflows

### Data Pipeline Workflow

1. **Ingestion**: Fetch raw data from 5 sources (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
2. **Validation**: Validate data structure and content
3. **Processing**: Transform, clean, and create domain features (drought/flood triggers)
4. **Merging**: Combine all processed datasets into master_dataset.csv
5. **Output**: Save in CSV and Parquet formats

### ML Pipeline Workflow

1. **Preprocessing**: 
   - Load master_dataset.csv
   - Create lag features (1, 3, 6, 12 months)
   - Create rolling statistics (3, 6 month windows)
   - Create interaction features (ENSO × Rainfall, IOD × NDVI)
   - Handle missing values (forward-fill)
   - Normalize features (standardization)
   - Split data temporally (70% train, 15% val, 15% test)

2. **Model Training**:
   - Random Forest (200 trees, max depth 15)
   - XGBoost (200 estimators, learning rate 0.05)
   - LSTM (2 layers: 128, 64 units, 12-month sequence)
   - Ensemble (weighted average: 30% RF, 40% XGB, 30% LSTM)

3. **Evaluation**:
   - Calculate metrics (R², RMSE, MAE, MAPE)
   - Generate prediction intervals (95% confidence)
   - Seasonal performance analysis
   - Feature importance analysis
   - Visualization (predictions vs actual, residuals, importance)

4. **Experiment Tracking**:
   - Log hyperparameters and metrics
   - Generate comparison reports
   - Track model versions

## Data Validation

The pipeline includes comprehensive validation:
- **Structure checks**: Ensures data is in DataFrame format
- **Column validation**: Verifies expected columns exist
- **Empty data detection**: Catches empty datasets
- **Missing value warnings**: Logs columns with null values

## Machine Learning Models

### Implemented Models

1. **Random Forest**
   - 200 estimators, max depth 15
   - Feature importance extraction
   - Cross-validation with 5 folds

2. **XGBoost**
   - 200 estimators, learning rate 0.05
   - Early stopping on validation set
   - Feature importance using gain metric

3. **LSTM (Long Short-Term Memory)**
   - 2 layers (128, 64 units)
   - 12-month sequence length
   - Early stopping with patience 10

4. **Ensemble Model**
   - Weighted average of RF, XGB, LSTM
   - Weights: 30% RF, 40% XGB, 30% LSTM
   - Improved prediction accuracy

### Model Performance Target

- **R² Score**: > 0.85 (production threshold)
- **RMSE**: Minimized for accurate predictions
- **Uncertainty Quantification**: 95% prediction intervals

## Output Files

### Data Pipeline Outputs (`outputs/processed/`)
- `nasa_power_processed.csv`
- `era5_processed.csv`
- `chirps_processed.csv`
- `ndvi_processed.csv`
- `ocean_indices_processed.csv`
- `master_dataset.csv` - Combined dataset (288 rows × 181 features)
- `master_dataset.parquet` - Optimized format

### ML Pipeline Outputs

**Preprocessed Features (`outputs/processed/`)**
- `features_train.csv` - Training set (70%)
- `features_val.csv` - Validation set (15%)
- `features_test.csv` - Test set (15%)
- `scaler_params.json` - Normalization parameters
- `feature_metadata.json` - Feature engineering statistics

**Trained Models (`outputs/models/`)**
- `random_forest_climate.pkl`
- `xgboost_climate.pkl`
- `lstm_climate.keras`
- `ensemble_climate_config.json`
- `*_metadata.json` - Model metadata

**Evaluation Reports (`outputs/evaluation/`)**
- `*_evaluation_summary.json` - Comprehensive metrics
- `*_predictions_vs_actual.png` - Scatter plots
- `*_residuals_over_time.png` - Time series plots
- `*_feature_importance.png` - Feature importance charts
- `*_predictions_with_uncertainty.csv` - Predictions with intervals

**Experiment Tracking (`outputs/experiments/`)**
- `experiment_log.jsonl` - All experiment records
- `comparison_report.md` - Experiment comparison
- `training_results_*.json` - Training summaries

## Quick Start

### Complete Workflow (Data + ML)

```bash
# 1. Run data pipeline to create master_dataset.csv
python run_pipeline.py

# 2. Quick prototype to test baseline
python pipelines/quick_model_pipeline.py

# 3. Full ML pipeline for production models
python model_development_pipeline.py --experiment-name production_v1
```

### Development Workflow

```bash
# 1. Data pipeline with debug mode
python run_pipeline.py --debug

# 2. Quick experiments for rapid iteration
python pipelines/quick_model_pipeline.py

# 3. Run tests
pytest -v

# 4. Full pipeline when ready
python model_development_pipeline.py
```

## Testing

The project includes 45+ comprehensive tests:

### Test Coverage
- **Data Pipeline**: Integration tests, merge functionality
- **Processing**: CHIRPS processing, Earth Engine setup
- **ML Models**: Model training, evaluation, predictions
- **Utilities**: Cache, versioning, performance monitoring
- **Validation**: Data quality, schema validation

### Running Tests
```bash
# Run all tests (45+ tests)
pytest -v

# Run with coverage report
pytest --cov=modules --cov=models --cov=preprocessing -v

# Run specific test categories
pytest tests/test_pipeline.py -v
pytest tests/test_chirps_processing.py -v
pytest tests/test_cache.py -v

# Run with debug logging
pytest -s
```

### Test Results
- ✅ 180+ tests passing
- ✅ Data pipeline integration verified
- ✅ Model training and evaluation tested
- ✅ Utility functions validated

## Logging

Logs are stored in `logs/` directory:
- Pipeline execution logs
- Validation results
- Error traces
- Data processing summaries

## Documentation

- **[Pipeline Overview](docs/pipeline_overview.md)** - Data pipeline architecture
- **[Model Development Guide](docs/MODEL_DEVELOPMENT_GUIDE.md)** - ML pipeline usage
- **[Implementation Status](docs/IMPLEMENTATION_STATUS.md)** - Project progress
- **[Pipeline README](pipelines/README.md)** - Pipeline comparison and usage
- **🆕 [Dev Deployment Guide](docs/DEV_DEPLOYMENT.md)** - Development environment setup
- **🆕 [Monitoring Guide](docs/MONITORING_GUIDE.md)** - Health checks and alerting
- **🆕 [Testing & Monitoring Reference](docs/TESTING_MONITORING_REFERENCE.md)** - Quick reference
- **🆕 [Mock API Usage](tests/mocks/README.md)** - Integration testing guide
- **[Spec Documents](.kiro/specs/)** - Requirements and design specs

## Development

### Adding New Data Sources

1. Create ingestion module in `modules/ingestion/`
2. Create processing module in `modules/processing/`
3. Add to pipeline in `pipelines/run_data_pipeline.py`
4. Add tests in `tests/`
5. Update documentation

### Adding New ML Features

1. **Domain features** → Add to `modules/processing/`
2. **ML features** → Add to `preprocessing/preprocess.py`
3. Update tests and documentation

### Adding New Models

1. Create model class in `models/` (inherit from `BaseModel`)
2. Add to `models/train_models.py`
3. Update `models/model_config.py` with hyperparameters
4. Add tests

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Document functions with docstrings
- Keep functions focused and modular
- Run `black` and `isort` for formatting
- Ensure tests pass before committing

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the phase2 directory
cd phase2
python run_pipeline.py
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**API authentication errors:**
- Check your `.env` file has correct API keys
- Verify API endpoints are accessible

**Empty DataFrame errors:**
- Run in debug mode first: `python run_pipeline.py --debug`
- Check data source availability
- Review logs in `logs/` directory

**"Master dataset not found" error:**
```bash
# Run data pipeline first
python run_pipeline.py
```

**Model training out of memory:**
```bash
# Use quick pipeline or train fewer models
python pipelines/quick_model_pipeline.py
# OR
python model_development_pipeline.py --models rf,xgb
```

**Pipeline too slow:**
```bash
# Use quick pipeline for prototyping
python pipelines/quick_model_pipeline.py
# OR skip preprocessing
python model_development_pipeline.py --skip-preprocessing
```

**Import sorting errors in CI:**
```bash
# Fix import formatting
isort .
black .
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest -v`
4. Commit with descriptive messages
5. Push and create a pull request

## License

This project is part of the Tanzania Climate Prediction initiative.

## Contact

For questions or issues, please open an issue on GitHub.

## Acknowledgments

- NASA POWER for climate data
- ECMWF for ERA5 reanalysis data
- Climate Hazards Group for CHIRPS rainfall data
- NOAA for ocean indices data
