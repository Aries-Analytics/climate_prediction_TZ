# Tanzania Climate Prediction - Phase 2

> **Status**: 🔵 Shadow Run v3 ACTIVE (Apr 16 – Jul 14, 2026 · two-zone Kilombero: Ifakara TC + Mlimba DC) · Live at [hewasense.majaribio.com](https://hewasense.majaribio.com)

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
├── args/                       # GOTCHA Args layer — persona config, model config
├── backend/                    # FastAPI application
│   └── app/
│       ├── api/                # REST API routes (28 endpoints)
│       ├── core/               # Database, config, security
│       ├── models/             # SQLAlchemy ORM models
│       └── services/           # Business logic, pipeline orchestration
│           └── pipeline/       # Scheduler, orchestrator, ingestion tracking
│
├── configs/                    # Trigger thresholds, pipeline config
├── context/                    # GOTCHA Context layer — domain knowledge
├── data/
│   ├── external/               # Ground truth (MapSPAM, HarvestStat, FAOSTAT)
│   └── processed/              # master_dataset.csv (1,878 rows, 6 locations, unscaled)
│
├── docs/                       # Documentation (see docs/README.md)
│   ├── current/                # Active status documents, executive summary
│   ├── guides/                 # How-to guides, deployment, monitoring
│   ├── pilots/kilombero/       # Kilombero Basin pilot operations
│   ├── references/             # Core reference documents (sources of truth)
│   ├── validation/             # Backtesting reports, basis risk validation
│   └── archive/                # Superseded documents (phase1/, phase2/, phase3/)
│
├── evaluation/                 # Model evaluation utilities
├── frontend/                   # React 18 + TypeScript + Material-UI dashboard
│   └── src/
│       ├── components/         # Dashboard components (7 views)
│       └── services/           # API client, data services
│
├── goals/                      # GOTCHA Goals layer
├── hardprompts/                # GOTCHA Hard Prompts layer
├── memory/                     # Project memory and session logs
├── models/                     # ML model implementations
│   ├── random_forest_model.py
│   ├── xgboost_model.py
│   ├── lstm_model.py
│   ├── ensemble_model.py
│   └── train_models.py         # Training orchestration
│
├── modules/
│   ├── ingestion/              # Data fetching from 5 sources
│   │   ├── nasa_power_ingestion.py
│   │   ├── era5_ingestion.py   # Uses ecmwf-datastores-client (not cdsapi)
│   │   ├── chirps_ingestion.py
│   │   ├── ndvi_ingestion.py
│   │   └── ocean_indices_ingestion.py
│   └── processing/             # Domain-specific processing & trigger logic
│
├── outputs/
│   ├── models/                 # Trained models + active_model.json (source of truth)
│   └── processed/              # ML features (z-score normalised — NOT for display)
│
├── pipelines/                  # Pipeline orchestration scripts
├── preprocessing/              # ML feature engineering (lag, rolling, interactions)
├── reporting/                  # Business report generation
│
├── scripts/                    # Utility scripts
│   ├── audit.py                # GOTCHA audit — forbidden pattern scanner
│   ├── run_evaluation.py       # Model evaluation runner
│   ├── train_pipeline.py       # ML training pipeline (RECOMMENDED)
│   └── verification/
│       └── verify_data_leakage.py
│
├── tests/                      # 180+ tests (83 pass, 68 xfail)
│   ├── mocks/                  # Mock APIs for integration testing (no network)
│   └── ...
│
├── tools/                      # GOTCHA Tools layer — devops, memory tooling
└── utils/                      # Shared utilities
    ├── slack_notifier.py       # Slack alerting
    ├── logger.py
    ├── cache.py
    └── ...
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

**Custom date range (offline reprocessing):**
```bash
python pipelines/run_data_pipeline.py --start-year 2010 --end-year 2020
```

> **Production ingestion** runs automatically via the backend scheduler (daily 6AM EAT). For local development use `docker compose -f docker-compose.dev.yml up -d` — the pipeline fires on schedule inside the container.

### 2. Model Training

**Training Pipeline (RECOMMENDED):**
```bash
# Full pipeline with feature selection, baselines, and validation
python scripts/train_pipeline.py

# Skip feature selection (not recommended)
python scripts/train_pipeline.py --skip-feature-selection

# Custom feature count (default: 83 selected from 245 candidates)
python scripts/train_pipeline.py --target-features 83

# Skip preprocessing if features already exist
python scripts/train_pipeline.py --skip-preprocessing
```

**Quick prototyping (fast, no preprocessing):**
```bash
python pipelines/quick_model_pipeline.py
```

**Note**: `scripts/train_pipeline.py` includes scientifically sound improvements:
- Feature selection (279 candidates → 83 selected, 11 leaky rainfall-derived features removed)
- Baseline model comparison
- Enhanced regularization
- Automated leakage validation

See [docs/references/ML_MODEL_REFERENCE.md](docs/references/ML_MODEL_REFERENCE.md) for details.

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

See [docs/guides/BUSINESS_REPORTS_GUIDE.md](docs/guides/BUSINESS_REPORTS_GUIDE.md) for detailed documentation.

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

See [docs/guides/DEV_DEPLOYMENT.md](docs/guides/DEV_DEPLOYMENT.md) and [docs/guides/MONITORING_GUIDE.md](docs/guides/MONITORING_GUIDE.md) for complete guides.

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

# ERA5 (ecmwf-datastores-client — NOT the deprecated cdsapi)
ECMWF_DATASTORES_URL=https://ewds.climate.copernicus.eu
ECMWF_DATASTORES_KEY=your_key_here

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

**New in March–April 2026:**
- **Shadow Run v2 ACTIVE**: Daily 6AM EAT pipeline generating 24 forecasts/day (3 triggers × 4 horizons × 2 zones), accumulating per-zone Brier Scores
- **Evidence Pack Dashboard**: Zone tabs, per-zone GO/NO-GO gates, basis risk display — all data-driven from API
- **Phase-Based Dynamic Model**: GDD-tracked 4-phase model — 100% catch rate on both confirmed crop disasters (2017/18 and 2021/22), 20% basis risk
- **Probabilistic triggers**: `norm.cdf()` using physical Kilombero thresholds — more defensible than static percentiles
- **Automated Evaluation**: ForecastLog records auto-resolve when validity windows mature (~Jul 2026 first Brier Scores). Per-zone GO/NO-GO gates trigger automatically at 90 days
- **Shadow run completion automation**: Stage 5 detects day-90 automatically, generates final Evidence Pack + Brier Score report

**New in February 2026:**
- **Actuarial Refinement (HewaSense V4)**: GDD integration, cumulative flood triggers, out-of-sample validation (2000-2014)
- **6-Location Phase-Based Backtesting**: Dual-index triggers, phase-weighted payouts, 22.6% loss ratio (sustainable)
- **Early Warning Dashboard**: Real-time forward alert view (displays when threshold breaches detected)

**New in January 2026:**
- **Mock APIs**: Test all data sources without network calls
- **Slack Alerts**: Real-time notifications for pipeline status
- **Monitoring Scripts**: Health checks and quality validation
- **Retry Configuration**: Best practices documented (3 for dev, 5-7 for production)

See [docs/guides/DEV_DEPLOYMENT.md](docs/guides/DEV_DEPLOYMENT.md) for complete setup guide.

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
# 1. Start the full stack (pipeline runs automatically at 6AM EAT)
docker compose -f docker-compose.dev.yml up -d

# 2. Quick prototype to test baseline (offline)
python pipelines/quick_model_pipeline.py

# 3. Full ML training pipeline
python scripts/train_pipeline.py
```

### Development Workflow

```bash
# 1. Start containers
docker compose -f docker-compose.dev.yml up -d

# 2. Quick experiments for rapid iteration
python pipelines/quick_model_pipeline.py

# 3. Run tests
pytest -v

# 4. Run audit before merging
python scripts/audit.py
```

## Testing

The project includes 180+ comprehensive tests:

### Test Coverage
- **Data Pipeline**: Integration tests, merge functionality
- **Processing**: CHIRPS processing, Earth Engine setup
- **ML Models**: Model training, evaluation, predictions
- **Utilities**: Cache, versioning, performance monitoring
- **Validation**: Data quality, schema validation

### Running Tests
```bash
# Run all tests
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

**Start here:** [docs/README.md](docs/README.md) — full docs index with role-based navigation

| Document | Description |
|----------|-------------|
| **[docs/current/EXECUTIVE_SUMMARY.md](docs/current/EXECUTIVE_SUMMARY.md)** | Latest project status, metrics, next steps |
| **[docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md](docs/references/PROJECT_OVERVIEW_CONSOLIDATED.md)** | Complete system overview |
| **[docs/references/ML_MODEL_REFERENCE.md](docs/references/ML_MODEL_REFERENCE.md)** | ML models, inference chain, training |
| **[docs/references/DATA_PIPELINE_REFERENCE.md](docs/references/DATA_PIPELINE_REFERENCE.md)** | Data pipeline architecture |
| **[docs/references/PARAMETRIC_INSURANCE_FINAL.md](docs/references/PARAMETRIC_INSURANCE_FINAL.md)** | Insurance model, triggers, financials |
| **[docs/pilots/kilombero/KILOMBERO_BASIN_PILOT_SPECIFICATION.md](docs/pilots/kilombero/KILOMBERO_BASIN_PILOT_SPECIFICATION.md)** | Active pilot specification |
| **[docs/validation/PHASE_BASED_COMPARISON.md](docs/validation/PHASE_BASED_COMPARISON.md)** | Backtesting & basis risk validation |
| **[docs/guides/AUTOMATED_PIPELINE_DEPLOYMENT.md](docs/guides/AUTOMATED_PIPELINE_DEPLOYMENT.md)** | Production deployment guide |
| **[docs/guides/DEV_DEPLOYMENT.md](docs/guides/DEV_DEPLOYMENT.md)** | Development environment setup |
| **[docs/guides/MONITORING_GUIDE.md](docs/guides/MONITORING_GUIDE.md)** | Health checks and alerting |
| **[tests/mocks/README.md](tests/mocks/README.md)** | Mock API integration testing guide |

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
python scripts/train_pipeline.py
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
python pipelines/run_data_pipeline.py
```

**Model training out of memory:**
```bash
# Use quick pipeline or skip preprocessing
python pipelines/quick_model_pipeline.py
# OR
python scripts/train_pipeline.py --skip-preprocessing
```

**Pipeline too slow:**
```bash
# Use quick pipeline for prototyping
python pipelines/quick_model_pipeline.py
# OR skip preprocessing
python scripts/train_pipeline.py --skip-preprocessing
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
