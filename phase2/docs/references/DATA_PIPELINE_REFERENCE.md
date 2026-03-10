# Data Pipeline Reference

**Last Updated**: February 5, 2026  
**Version**: 2.1  
**Status**: ✅ Production Ready

---

## Overview

The Tanzania Climate Intelligence Platform data pipeline is a comprehensive system that ingests, processes, and merges climate data from five authoritative sources to create a unified dataset for machine learning and analysis. The pipeline supports both automated scheduling and manual execution with comprehensive monitoring and error handling.

### Key Features

- **Multi-Source Integration**: 5 authoritative climate data sources
- **Automated Scheduling**: Daily execution at 06:00 UTC (configurable)
- **Incremental Updates**: Fetches only new data since last run
- **Real-Time Processing**: Live data from APIs and satellite sources
- **Quality Validation**: Comprehensive data quality checks
- **Graceful Degradation**: Continues with partial data if sources fail
- **Retry Logic**: Exponential backoff for transient failures
- **Multi-Channel Alerts**: Email and Slack notifications
- **Performance Monitoring**: Prometheus metrics and health checks

---

## Architecture

### High-Level Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                          │
│  ┌──────────┐  ┌──────┐  ┌────────┐  ┌──────┐  ┌─────────┐│
│  │NASA POWER│  │ ERA5 │  │ CHIRPS │  │ NDVI │  │ Ocean   ││
│  │          │  │      │  │        │  │      │  │ Indices ││
│  └────┬─────┘  └───┬──┘  └───┬────┘  └───┬──┘  └────┬────┘│
└───────┼────────────┼─────────┼───────────┼──────────┼──────┘
        │            │         │           │          │
        ▼            ▼         ▼           ▼          ▼
   data/raw/    data/raw/  data/raw/  data/raw/  data/raw/
        │            │         │           │          │
┌───────┼────────────┼─────────┼───────────┼──────────┼──────┐
│       │       PROCESSING LAYER            │          │      │
│       ▼            ▼         ▼           ▼          ▼      │
│  ┌──────────┐  ┌──────┐  ┌────────┐  ┌──────┐  ┌─────────┐│
│  │ Process  │  │Process│ │Process │  │Process│ │Process  ││
│  │NASA POWER│  │ ERA5 │  │ CHIRPS │  │ NDVI │  │ Ocean   ││
│  └────┬─────┘  └───┬──┘  └───┬────┘  └───┬──┘  └────┬────┘│
└───────┼────────────┼─────────┼───────────┼──────────┼──────┘
        │            │         │           │          │
        ▼            ▼         ▼           ▼          ▼
   outputs/processed/*.csv (5 files)
        │            │         │           │          │
        └────────────┴─────────┴───────────┴──────────┘
                              │
┌─────────────────────────────┼──────────────────────────────┐
│                       MERGE LAYER                           │
│                             ▼                               │
│                      ┌─────────────┐                        │
│                      │  merge_all  │                        │
│                      └──────┬──────┘                        │
└─────────────────────────────┼──────────────────────────────┘
                              │
                              ▼
                    master_dataset.csv
                    master_dataset.parquet
```

### System Components

#### 1. Pipeline Orchestrator
**Location**: `backend/app/services/pipeline/orchestrator.py`

Coordinates the entire pipeline execution:
- Manages execution locking to prevent concurrent runs
- Coordinates ingestion, forecasting, and forecast evaluation stages (3-stage pipeline)
- Handles errors and implements retry logic
- Records comprehensive execution metadata
- Provides status reporting and monitoring

#### 2. Incremental Ingestion Manager
**Location**: `backend/app/services/pipeline/incremental_manager.py`

Manages efficient data fetching:
- Tracks last successful ingestion date per source
- Calculates optimal fetch ranges for incremental updates
- Handles default 180-day lookback for new sources
- Updates tracking records after successful ingestion
- Prevents duplicate data ingestion

#### 3. Data Quality Manager
**Location**: `utils/quality_metrics.py`

Ensures data integrity:
- Comprehensive quality assessment (completeness, consistency, accuracy)
- Automated quality scoring (0-100 scale)
- Temporal consistency validation
- Outlier detection and reporting
- Quality trend monitoring

#### 4. Performance Monitor
**Location**: `utils/performance.py`

Tracks pipeline performance:
- Operation timing and profiling
- Memory usage monitoring
- Throughput metrics calculation
- DataFrame optimization utilities
- Performance benchmarking and reporting

---

## Data Sources

### 1. NASA POWER
**Type**: Climate Reanalysis  
**Purpose**: Temperature, solar radiation, precipitation  
**API**: NASA POWER API  
**Authentication**: None required  
**Update Frequency**: Daily  
**Coverage**: Global, 0.5° × 0.5° resolution

**Key Variables**:
- Temperature (min, max, mean)
- Solar radiation
- Precipitation
- Humidity
- Wind speed
- **Soil moisture (GWETPROF)** - Profile soil moisture (0-1 fraction) ⭐ *Added Feb 2026*

### 2. ERA5
**Type**: Atmospheric Reanalysis  
**Purpose**: Comprehensive atmospheric variables  
**API**: Copernicus Climate Data Store (CDS)  
**Authentication**: CDS API key required  
**Update Frequency**: Daily (with 5-day delay)  
**Coverage**: Global, 0.25° × 0.25° resolution

**Key Variables**:
- Temperature at multiple levels
- Pressure
- Wind components
- Humidity
- Precipitation
- Cloud cover
- **Soil moisture (SWVL1)** - Volumetric soil water layer 1 (0-7cm depth) ⭐ *Added Feb 2026*

### 3. CHIRPS
**Type**: Satellite Precipitation  
**Purpose**: High-resolution rainfall measurements  
**API**: Google Earth Engine / UCSB Climate Hazards Center  
**Authentication**: GEE authentication for real-time data  
**Update Frequency**: Daily  
**Coverage**: 50°S-50°N, 0.05° × 0.05° resolution

**Key Variables**:
- Daily precipitation
- Rainfall anomalies
- Drought indicators
- Flood risk metrics

### 4. MODIS NDVI
**Type**: Satellite Vegetation  
**Purpose**: Vegetation health and crop monitoring  
**API**: Google Earth Engine  
**Authentication**: GEE service account  
**Update Frequency**: 16-day composite  
**Coverage**: Global, 250m resolution

**Key Variables**:
- Normalized Difference Vegetation Index (NDVI)
- Vegetation Condition Index (VCI)
- Crop stress indicators
- Phenology metrics

### 5. Ocean Indices
**Type**: Climate Indices  
**Purpose**: ENSO and Indian Ocean Dipole patterns  
**API**: NOAA Climate Prediction Center  
**Authentication**: None required  
**Update Frequency**: Monthly  
**Coverage**: Global ocean-atmosphere patterns (2000-Present)

**Key Variables**:
- Oceanic Niño Index (ONI)
- Indian Ocean Dipole (IOD)
- ENSO phase indicators
- Climate forecasts

---

## Pipeline Stages

### Stage 1: Data Ingestion

**Location**: `modules/ingestion/`

**Purpose**: Fetch raw data from external APIs and save to local storage

**Modules**:
- `nasa_power_ingestion.py` - NASA POWER API integration
- `era5_ingestion.py` - Copernicus CDS integration
- `chirps_ingestion.py` - UCSB/GEE integration
- `ndvi_ingestion.py` - MODIS/GEE integration
- `ocean_indices_ingestion.py` - NOAA integration

**Common Interface**:
```python
def fetch_data(dry_run=False, start_year=2010, end_year=2023, **kwargs):
    """Fetch data from external source"""
    # Returns: pandas DataFrame with standardized columns
```

**Features**:
- Incremental fetching (only new data since last run)
- Retry logic with exponential backoff
- Data validation during ingestion
- Comprehensive error logging
- Graceful handling of API failures

**Outputs**: Raw CSV files in `data/raw/`

### Stage 2: Data Processing

**Location**: `modules/processing/`

**Purpose**: Clean, validate, and standardize ingested data

**Modules**:
- `process_nasa_power.py` - Temperature and radiation processing
- `process_era5.py` - Atmospheric variable processing
- `process_chirps.py` - Rainfall and drought indicator processing
- `process_ndvi.py` - Vegetation health processing
- `process_ocean_indices.py` - Climate index processing

**Common Interface**:
```python
def process(data):
    """Process raw data into cleaned, standardized format"""
    # Returns: pandas DataFrame with processed features
```

**Processing Steps**:
1. **Data Cleaning**: Remove invalid values, handle missing data
2. **Standardization**: Consistent units, naming conventions
3. **Feature Engineering**: Derived variables, indicators, indices
4. **Quality Validation**: Completeness, range, consistency checks
5. **Temporal Alignment**: Consistent time indexing

**Outputs**: Processed CSV files in `outputs/processed/`

### Stage 3: Data Merging

**Location**: `modules/processing/merge_processed.py`

**Purpose**: Combine all processed datasets into unified master dataset

**Function**: `merge_all()`

**Merging Strategy**:
1. **Temporal Merge**: Year-month based alignment
2. **Spatial Merge**: Location-based alignment (if applicable)
3. **Quality Preservation**: Maintain data provenance
4. **Validation**: Ensure merge integrity

**Features**:
- Intelligent merge strategy selection
- Data provenance tracking
- Quality metric preservation
- Multiple output formats (CSV, Parquet)

**Outputs**:
- `outputs/processed/master_dataset_6loc_2000_2025.csv` ⭐ **AUTHORITATIVE DATASET**
  - 1,872 records (6 locations × 312 months)
  - 6 locations: Arusha, Dar es Salaam, Dodoma, Mbeya, Morogoro, Mwanza
  - Years: 2000-2025 (26 years)
  - 379 features
- `outputs/processed/master_dataset.csv` (legacy, may be subset)
- Merge metadata and quality reports

---

## Automated Pipeline System

### Scheduling

**Scheduler**: APScheduler with in-memory job store
**Default Schedule**: Daily at 06:00 EAT (Africa/Dar_es_Salaam)
**Configuration**: Environment variables `PIPELINE_SCHEDULE` + `PIPELINE_TIMEZONE`

**Schedule Examples**:
```bash
# Daily at 6 AM EAT (production / shadow run)
PIPELINE_SCHEDULE="0 6 * * *"
PIPELINE_TIMEZONE=Africa/Dar_es_Salaam

# Twice daily (6 AM and 6 PM EAT)
PIPELINE_SCHEDULE="0 6,18 * * *"
PIPELINE_TIMEZONE=Africa/Dar_es_Salaam

# Weekly on Sundays at 2 AM EAT
PIPELINE_SCHEDULE="0 2 * * 0"
PIPELINE_TIMEZONE=Africa/Dar_es_Salaam
```

### Execution Flow

1. **Pre-Execution Checks**
   - Verify no concurrent execution
   - Check system resources
   - Validate configuration

2. **Incremental Planning**
   - Query last successful ingestion dates
   - Calculate fetch ranges for each source
   - Plan execution strategy

3. **Data Ingestion**
   - Fetch data from each source
   - Validate and store raw data
   - Update ingestion tracking

4. **Data Processing**
   - Process each source independently
   - Apply quality checks
   - Generate processed datasets

5. **Data Merging**
   - Combine processed datasets
   - Create master dataset
   - Generate quality reports

6. **Post-Execution**
   - Record execution metadata
   - Update monitoring metrics
   - Send completion notifications

### Error Handling

**Retry Logic**:
- Maximum 3 attempts per operation
- Exponential backoff (2s, 4s, 8s)
- Configurable retry parameters

**Graceful Degradation**:
- Continue with available data if some sources fail
- Mark execution as "partial" rather than "failed"
- Detailed logging of source-specific failures

**Alert System**:
- Email notifications for failures
- Slack integration for team alerts
- Structured alert templates
- Configurable alert thresholds

---

## Monitoring and Observability

### Prometheus Metrics

**Endpoint**: `http://localhost:9090/metrics`

**Key Metrics**:
- `pipeline_execution_total` - Total executions
- `pipeline_execution_failures_total` - Total failures
- `pipeline_execution_duration_seconds` - Execution duration
- `pipeline_data_records_ingested_total` - Records processed
- `data_freshness_days` - Age of data
- `pipeline_success_rate` - Success rate percentage

### Health Checks

**Endpoint**: `http://localhost:8080/health`

**Health Status**:
- `healthy` - All systems operational
- `degraded` - Some issues but functional
- `unhealthy` - Critical issues requiring attention

**Health Indicators**:
- Last execution status
- Data freshness
- Source availability
- System resource usage

### Logging

**Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL  
**Log Format**: Structured JSON with timestamps  
**Log Rotation**: Daily rotation with 30-day retention  
**Log Locations**:
- Console output (stdout)
- File logs: `logs/pipeline_YYYY-MM-DD.log`
- Centralized logging (if configured)

---

## Performance Characteristics

### Execution Times

**Typical Performance** (production mode):

| Stage | Duration | Notes |
|-------|----------|-------|
| NASA POWER ingestion | 10-30 seconds | Depends on date range |
| ERA5 ingestion | 2-10 minutes | CDS API can be slow |
| CHIRPS ingestion | 5-15 minutes | GEE processing time |
| NDVI ingestion | 1-5 minutes | GEE composite processing |
| Ocean Indices ingestion | <5 seconds | Small dataset |
| Processing (all sources) | 1-2 minutes | Local computation |
| Merging | <10 seconds | Memory-based operation |
| **Total Pipeline** | **10-30 minutes** | Varies by data volume |

**Debug Mode**: <1 minute (uses mock data)

### Resource Usage

**Memory**: 1-2 GB peak usage during processing  
**CPU**: 2-4 cores recommended  
**Storage**: 100 MB per year of data  
**Network**: 10-50 MB per execution

### Scalability

**Data Volume**: Tested with 15+ years of data (191 monthly records)  
**Geographic Scale**: Single location to multi-location support  
**Temporal Scale**: Daily to monthly data frequencies  
**Source Scale**: 5 sources, extensible architecture

---

## Configuration

### Environment Variables

**Required**:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/climate_prod

# Pipeline Schedule
PIPELINE_SCHEDULE=0 6 * * *
PIPELINE_TIMEZONE=Africa/Dar_es_Salaam
```

**Optional**:
```bash
# Data Sources
NASA_POWER_API_URL=https://power.larc.nasa.gov/api/
ERA5_CDS_API_KEY=your_cds_api_key
GEE_SERVICE_ACCOUNT_KEY=path/to/service-account.json

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Performance
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=2
DATA_STALENESS_THRESHOLD_DAYS=7
```

### Directory Structure

```
project/
├── modules/
│   ├── ingestion/              # Data ingestion modules
│   │   ├── nasa_power_ingestion.py
│   │   ├── era5_ingestion.py
│   │   ├── chirps_ingestion.py
│   │   ├── ndvi_ingestion.py
│   │   └── ocean_indices_ingestion.py
│   └── processing/             # Data processing modules
│       ├── process_nasa_power.py
│       ├── process_era5.py
│       ├── process_chirps.py
│       ├── process_ndvi.py
│       ├── process_ocean_indices.py
│       └── merge_processed.py
├── utils/                      # Utility modules
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging setup
│   ├── validator.py           # Data validation
│   ├── cache.py               # Caching system
│   ├── quality_metrics.py     # Quality assessment
│   ├── performance.py         # Performance monitoring
│   └── scheduler.py           # Scheduling utilities
├── data/                       # Data storage
│   ├── raw/                   # Raw ingested data
│   └── external/              # External reference data
├── outputs/                    # Pipeline outputs
│   └── processed/             # Final processed datasets
├── logs/                       # Log files
├── tests/                      # Test files
├── backend/                    # Production backend
│   └── app/services/pipeline/ # Pipeline services
└── run_pipeline.py            # Main pipeline entry point
```

---

## Quality Assurance

### Data Quality Metrics

**Completeness**: Percentage of expected data points present  
**Consistency**: Temporal and cross-source consistency  
**Accuracy**: Outlier detection and range validation  
**Timeliness**: Data freshness and update frequency  

**Quality Scoring**: 0-100 scale with thresholds:
- 90-100: Excellent
- 80-89: Good
- 70-79: Acceptable
- <70: Poor (requires attention)

### Validation Framework

**Schema Validation**: Column presence, data types, formats  
**Range Validation**: Reasonable value ranges for each variable  
**Temporal Validation**: Chronological consistency, gap detection  
**Cross-Source Validation**: Consistency between related sources  

### Testing

**Unit Tests**: Individual module testing  
**Integration Tests**: End-to-end pipeline testing  
**Performance Tests**: Load and stress testing  
**Quality Tests**: Data quality validation  

**Test Coverage**: 80%+ across all modules  
**Continuous Integration**: Automated testing on code changes  

---

## Troubleshooting

### Common Issues

#### Pipeline Not Running
**Symptoms**: No recent executions, scheduler inactive  
**Solutions**:
1. Check scheduler service status
2. Verify schedule configuration
3. Check for execution locks
4. Review scheduler logs

#### Data Not Updating
**Symptoms**: Stale data, no new records  
**Solutions**:
1. Check source API availability
2. Verify authentication credentials
3. Review ingestion logs
4. Test individual source modules

#### Performance Issues
**Symptoms**: Slow execution, high resource usage  
**Solutions**:
1. Monitor resource usage
2. Optimize batch sizes
3. Check network connectivity
4. Review processing efficiency

#### Quality Issues
**Symptoms**: Low quality scores, validation failures  
**Solutions**:
1. Review quality reports
2. Check source data integrity
3. Validate processing logic
4. Monitor data trends

### Error Codes

| Code | Description | Action |
|------|-------------|--------|
| E001 | Source API unavailable | Check network, retry later |
| E002 | Authentication failure | Verify credentials |
| E003 | Data validation failed | Review data quality |
| E004 | Processing error | Check processing logic |
| E005 | Merge failure | Verify data compatibility |

---

## Future Enhancements

### Planned Features

**Real-Time Streaming**: Live data ingestion and processing  
**Distributed Processing**: Parallel execution across multiple nodes  
**Advanced Analytics**: ML-based anomaly detection  
**API Integration**: RESTful API for external access  
**Dashboard Integration**: Real-time monitoring dashboards  

### Scalability Improvements

**Horizontal Scaling**: Multi-node deployment support  
**Cloud Integration**: AWS/Azure/GCP compatibility  
**Container Orchestration**: Kubernetes deployment  
**Load Balancing**: Distributed execution management  

---

## Recent Improvements

### January 2026 - Data Pipeline Robustness Enhancements

**Status**: ✅ Complete  
**Details**: [DATA_PIPELINE_TEST_FIXES.md](../reports/DATA_PIPELINE_TEST_FIXES.md)

Comprehensive fixes to improve pipeline reliability and data quality:

**Key Improvements**:

1. **Temporal Column Consistency**:
   - All 5 processing modules now consistently include year/month columns
   - Added validation to ensure temporal columns are present before merging
   - Prevents KeyError failures in downstream operations

2. **Improved NaN Handling**:
   - Selective dropping of rows with critical missing values only
   - Imputation of non-critical missing values
   - Preserves more samples while maintaining data quality
   - Reduced sample loss from 100% to <10% in preprocessing

3. **Edge Case Handling**:
   - Temporal splitting now handles small datasets gracefully
   - Minimum sample size validation (10 samples required)
   - Ensures validation sets are never empty when data is sufficient
   - Clear error messages for insufficient data

4. **Deduplication Logic**:
   - Proper merge operations on year-month-location keys
   - Eliminated 1,872 duplicate records
   - Logging of deduplication statistics
   - Validation checks after merge operations

5. **Flood Trigger Fixes**:
   - Corrected flood risk score calculation
   - Fixed trigger activation logic for extreme rainfall
   - Proper threshold comparison
   - Added logging for trigger events

**Impact**:
- Test pass rate: 35/45 → 45/45 (100%)
- Zero duplicate records in merged data
- Consistent temporal columns across all data sources
- Robust handling of edge cases

### February 2026 - Historical Data Recovery
**Status**: ✅ Complete
**Details**: [FEBRUARY_2026_FIX_SUMMARY.md](../current/FEBRUARY_2026_FIX_SUMMARY.md)

**Improvements**:
1. **Ocean Indices Recovery**:
   - Identified missing historical ENSO/IOD data (2000-2020)
   - Executed targeted ingestion to recover 26 years of data (312 months)
   - Verified integration with master dataset

2. **Orchestrator Path Logic**:
   - Fixed bug where `ocean_indices` was incorrectly looking for `_combined.csv` format
   - Implemented special handling for global raw data sources
- Production-ready data pipeline

**Files Modified**:
- 5 processing modules (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)
- Merge processing module
- Preprocessing module
- Pipeline wrapper
- 4 test files

---

## Troubleshooting

### Common Issues

#### Ocean Indices Processing Fails

**Symptom:**
```
FileNotFoundError: Raw data not found: data/raw/ocean_indices_combined.csv
```

**Root Cause:**
Ocean indices uses a different file path (`ocean_indices_raw.csv`) than other sources (`*_combined.csv`). The orchestrator must handle this special case before checking the generic path.

**Solution:**
Ensure ocean indices is processed with special case handling in `modules/processing/orchestrator.py`:

```python
# CORRECT: Check ocean_indices FIRST
if source_name == "ocean_indices":
    raw_data_path = Path("data/raw/ocean_indices_raw.csv")
    # ... process
else:
    raw_data_path = Path(f"data/raw/{source_name}_combined.csv")
    # ... process
```

**Verification:**
```bash
# Check if ocean indices file exists
ls data/raw/ocean_indices_raw.csv

# Re-download if missing
python -c "from modules.ingestion.ocean_indices_ingestion import fetch_ocean_indices_data; \
fetch_ocean_indices_data(start_year=2000, end_year=2025, dry_run=False)"
```

#### Dashboard Showing Normalized Values

**Symptom:**
- Temperature showing values like `0.776` instead of `25°C`
- Rainfall showing values like `-0.747` instead of `125mm`
- All values appear to be z-scores (mean≈0, std≈1)

**Root Cause:**
Dashboard is loading from normalized/engineered features instead of raw processed data.

**Solution:**
1. **Verify data source configuration:**
   ```python
   # In utils/config.py
   MASTER_DATASET = "data/processed/master_dataset.csv"  # NOT outputs/processed/*
   ```

2. **Check master dataset has raw values:**
   ```bash
   # Temperature should be 15-30°C, not -2 to +2
   python -c "import pandas as pd; df = pd.read_csv('data/processed/master_dataset.csv'); \
   print(f'Temp range: {df.temp_mean_c.min()}-{df.temp_mean_c.max()}')"
   ```

3. **Regenerate if needed:**
   ```bash
   python modules/processing/orchestrator.py
   python scripts/load_dashboard_data.py --clear
   ```

#### Missing Historical Ocean Indices Data

**Symptom:**
- ENSO (ONI) and IOD time series only showing recent years (e.g., 2020-2025)
- Missing 15-20 years of historical data

**Root Cause:**
Ocean indices file was ingested with limited date range.

**Solution:**
```bash
# Re-download complete time series (2000-2025)
python -c "from modules.ingestion.ocean_indices_ingestion import fetch_ocean_indices_data; \
df = fetch_ocean_indices_data(start_year=2000, end_year=2025, dry_run=False); \
print(f'Downloaded {len(df)} records from {df.year.min()}-{df.year.max()}')"

# Reprocess and reload
python modules/processing/orchestrator.py
python scripts/load_dashboard_data.py --clear
```

#### Processed Files Empty or Missing

**Symptom:**
- `outputs/processed/*.csv` files don't exist
- Files have only 3-7 test rows

**Root Cause:**
Processing pipeline was never run on production data.

**Solution:**
1. **Verify raw combined files exist:**
   ```bash
   ls data/raw/*_combined.csv
   ```

2. **Run processing pipeline:**
   ```bash
   python modules/processing/orchestrator.py
   ```

3. **Verify output:**
   ```bash
   # Should show ~1,800-1,900 rows each
   wc -l outputs/processed/*.csv
   ```

### Data Validation Checklist

Before loading data into dashboard:

```python
import pandas as pd

df = pd.read_csv("data/processed/master_dataset.csv")

# 1. Check row count (should be ~1,800-1,900 for 6 locations × 25 years)
assert len(df) > 1000, f"Too few rows: {len(df)}"

# 2. Check for RAW values (not normalized)
assert df['temp_mean_c'].between(10, 40).all(), "Temperature appears normalized"
assert df['rainfall_mm'].between(0, 500).all(), "Rainfall appears normalized"
assert df['ndvi'].between(0, 1).all(), "NDVI out of range"

# 3. Check ocean indices coverage
ocean_data = df[df['oni'].notna()]
assert ocean_data['year'].min() <= 2000, f"Ocean indices missing early data: starts {ocean_data['year'].min()}"
assert ocean_data['year'].max() >= 2025, f"Ocean indices missing recent data: ends {ocean_data['year'].max()}"

print("✅ All validation checks passed")
```

### Prevention Best Practices

1. **Always validate data ranges** before dashboard loading
2. **Document special-case file paths** (ocean indices, etc.)
3. **Run processing pipeline** after any raw data updates
4. **Test with data validation script** before production deployment
5. **Monitor dashboard** for z-score-like values (±3 range)

---

## Related Documentation


- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Quick start guide
- **[ML_MODEL_REFERENCE.md](./ML_MODEL_REFERENCE.md)** - ML model details
- **[TESTING_REFERENCE.md](./TESTING_REFERENCE.md)** - Testing documentation
- **[DEPLOYMENT_REFERENCE.md](./DEPLOYMENT_REFERENCE.md)** - Deployment guide
- **[data_dictionary.md](./data_dictionary.md)** - Data schemas

---

### March 2026 — Scheduler, ForecastLog & Probability Fixes

**Status**: ✅ Complete

#### Mar 8 — Scheduler Timezone Fix
**Problem**: `CronTrigger.from_crontab("0 6 * * *")` was inheriting UTC timezone from `BackgroundScheduler`, not Africa/Dar_es_Salaam. Pipeline was firing at 06:00 UTC (09:00 EAT) instead of 06:00 EAT.
**Fix**: Pass `timezone` explicitly to `CronTrigger.from_crontab()`:
```python
# CORRECT (file: backend/app/services/pipeline/scheduler.py:215)
trigger = CronTrigger.from_crontab(self.schedule, timezone=self.timezone)
# NOT: BackgroundScheduler(timezone=self.timezone) — this does NOT propagate to CronTrigger
```
**Signal**: Scheduler logs `next run at: 2026-03-XX 06:00:00+03:00` — the `+03:00` confirms Africa/Dar_es_Salaam is active.

#### Mar 9 — ForecastLog New Fields
Two fields that were always NULL are now populated from each scheduled run:

| Field | Value | Purpose |
|---|---|---|
| `threshold_used` | `0.65` (drought/flood) / `0.60` (heat_stress/crop_failure) | Records the probability threshold used for this trigger type in the evidence pack |
| `forecast_distribution` | `{horizon_tier, is_insurance_trigger_eligible, confidence_lower, confidence_upper}` | Records horizon classification and insurance eligibility per forecast |

Source: `orchestrator.py:_generate_forecasts()` — `_PROB_THRESHOLDS` dict. Commit `33dc78e`.

#### Mar 10 — Stale Advisory Lock Recovery
**Pattern**: Scheduler fires at 6AM but logs `"Pipeline execution lock already held (ID: 123456)"` with no prior `"Pipeline execution starting"` → lock is stale from a prior interrupted session.
**Recovery**:
```bash
docker restart climate_pipeline_scheduler_dev
# Startup _clear_stale_locks() releases it.
# Confirmation signal: "No stale advisory locks found on startup"
```
**Do NOT** issue `pg_advisory_unlock()` manually — the startup routine handles it cleanly.

#### Mar 10 — Probability Conversion (ForecastLog.probability_score)
Raw model output (z-score) is now converted to trigger probability via physical Kilombero rice phase thresholds instead of sigmoid. See `backend/app/services/forecast_service.py:_raw_to_probability()`. Source: `rice_thresholds.RAINFALL_THRESHOLDS` (TARI/FAO).

---

**Document Version**: 2.2
**Last Updated**: March 10, 2026
**Status**: ✅ Production Ready
**Consolidates**: pipeline_overview.md, AUTOMATED_PIPELINE_GUIDE.md, PIPELINE_EXECUTION_SUMMARY.md, PIPELINE_REPLACEMENT_COMPLETE.md, PIPELINE_REPLACEMENT_SUMMARY.md, PIPELINE_RUN_SUMMARY_2010_2025.md