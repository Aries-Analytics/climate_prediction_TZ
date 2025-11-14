# Pipeline Overview

## Purpose

The Phase 2 Tanzania Climate Prediction pipeline ingests, processes, and merges climate data from five external sources to create a unified master dataset for climate prediction modeling.

## Architecture

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

## Data Sources

| Source | Type | Purpose | Auth Required |
|--------|------|---------|---------------|
| NASA POWER | Climate data | Temperature, radiation, precipitation | No |
| ERA5 | Reanalysis | Atmospheric variables | Yes (CDS API) |
| CHIRPS | Satellite | Rainfall data | No |
| NDVI | Satellite | Vegetation health | No (currently synthetic) |
| Ocean Indices | Climate indices | ENSO, IOD | No |

## Pipeline Stages

### 1. Ingestion

**Location:** `modules/ingestion/`

**Purpose:** Fetch raw data from external APIs and save to `data/raw/`

**Modules:**
- `nasa_power_ingestion.py` - NASA POWER API
- `era5_ingestion.py` - Copernicus CDS
- `chirps_ingestion.py` - UCSB Climate Hazards Center
- `ndvi_ingestion.py` - Vegetation index (synthetic)
- `ocean_indices_ingestion.py` - NOAA climate indices

**Common Interface:**
```python
def fetch_data(dry_run=False, start_year=2010, end_year=2023, **kwargs):
    """Fetch data from external source"""
    # Returns: pandas DataFrame
```

**Outputs:** Raw CSV files in `data/raw/`

### 2. Processing

**Location:** `modules/processing/`

**Purpose:** Clean, validate, and standardize ingested data

**Modules:**
- `process_nasa_power.py`
- `process_era5.py`
- `process_chirps.py`
- `process_ndvi.py`
- `process_ocean_indices.py`

**Common Interface:**
```python
def process(data):
    """Process raw data into cleaned format"""
    # Returns: pandas DataFrame
```

**Outputs:** Processed CSV files in `outputs/processed/`

### 3. Merging

**Location:** `modules/processing/merge_processed.py`

**Purpose:** Combine all processed datasets into master dataset

**Function:** `merge_all()`

**Merging Strategy:**
1. Year-based merge (if 2+ datasets have 'year' column)
2. Geo-based merge (if datasets have lat/lon)
3. Concatenation fallback

**Outputs:**
- `outputs/processed/master_dataset.csv`
- `outputs/processed/master_dataset.parquet`

## Utilities

### Configuration (`utils/config.py`)

- Path management (`get_data_path`, `get_output_path`)
- Environment validation
- Data source URLs
- Directory structure setup

### Logging (`utils/logger.py`)

- Centralized logging setup
- Timestamped log files in `logs/`
- Automatic rotation and cleanup
- Console and file output

### Validation (`utils/validator.py`, `utils/validation.py`)

- DataFrame structure validation
- Column existence checks
- Empty data detection
- Missing value warnings

## Execution Modes

### Debug Mode (Dry-Run)

```bash
python run_pipeline.py --debug
```

- Uses mock data for ingestion (no API calls)
- Verbose logging (DEBUG level)
- Fast execution for testing

### Production Mode

```bash
python run_pipeline.py
```

- Real API calls to external sources
- Standard logging (INFO level)
- Full data processing

## Directory Structure

```
phase2/
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
│   ├── config.py
│   ├── logger.py
│   ├── validator.py
│   └── validation.py
├── data/                       # Data storage
│   ├── raw/                    # Raw ingested data
│   ├── processed/              # Intermediate processed data
│   └── external/               # External reference data
├── outputs/                    # Pipeline outputs
│   └── processed/              # Final processed datasets
│       ├── nasa_power_processed.csv
│       ├── era5_processed.csv
│       ├── chirps_processed.csv
│       ├── ndvi_processed.csv
│       ├── ocean_indices_processed.csv
│       ├── master_dataset.csv
│       └── master_dataset.parquet
├── logs/                       # Log files
│   └── pipeline_YYYY-MM-DD.log
├── tests/                      # Test files
│   ├── test_pipeline.py
│   └── test_merge_processed.py
├── docs/                       # Documentation
│   ├── pipeline_overview.md
│   ├── data_dictionary.md
│   ├── feature_engineering.md
│   └── pipeline_run_instructions.md
├── run_pipeline.py             # Main pipeline entry point
└── .env                        # Environment variables
```

## Error Handling

The pipeline includes comprehensive error handling:

- **Ingestion failures**: Logged and raised, pipeline stops
- **Processing failures**: Logged and raised, pipeline stops
- **Merge failures**: Logged and raised
- **Validation failures**: Raises `ValueError` with details
- **Missing files**: Logged warnings, continues with available data

## Logging

All pipeline operations are logged to:
- Console (stdout)
- Daily log files: `logs/pipeline_YYYY-MM-DD.log`

Log format:
```
2024-11-14 10:30:45 | INFO | module_name | Message
```

## Performance

Typical execution times (production mode):

| Stage | Time |
|-------|------|
| NASA POWER ingestion | 10-30 seconds |
| ERA5 ingestion | 2-10 minutes |
| CHIRPS ingestion | 5-15 minutes |
| NDVI ingestion | < 1 second |
| Ocean Indices ingestion | < 5 seconds |
| Processing (all) | 1-2 minutes |
| Merging | < 10 seconds |
| **Total** | ~10-30 minutes |

Debug mode: < 1 minute (uses mock data)

## Implemented Features

✅ **Caching Layer** (`utils/cache.py`)
- File-based cache for API data
- Configurable TTL (time-to-live)
- Automatic cache invalidation
- Reduces redundant API calls

✅ **Incremental Updates** (`utils/incremental.py`)
- Tracks last update timestamps
- Fetches only new data since last update
- Merges with existing data
- Reduces processing time and API usage

✅ **Data Quality Metrics** (`utils/quality_metrics.py`)
- Comprehensive quality assessment
- Completeness, missing values, duplicates
- Temporal consistency checks
- Quality score calculation (0-100)
- Automated quality reports

✅ **Data Versioning** (`utils/versioning.py`)
- Version control for datasets
- Rollback capabilities
- Version comparison
- Checksum validation
- Complete version history

✅ **Performance Monitoring** (`utils/performance.py`)
- Operation timing and profiling
- Memory usage tracking
- Throughput metrics
- DataFrame optimization utilities
- Performance benchmarking

✅ **Automated Scheduling** (`utils/scheduler.py`)
- Periodic data refresh scheduling
- Daily, weekly, hourly, or interval-based
- Background thread execution
- Job management (add, cancel, list)

✅ **Data Visualizations** (`utils/visualizations.py`)
- Time series plots
- Quality metrics dashboards
- Correlation matrices
- Distribution plots
- Automated chart generation

✅ **Comprehensive Testing** (`tests/`)
- 10 test modules covering all utilities
- Unit tests for cache, incremental, quality metrics
- Integration tests for pipeline and merge
- Test coverage for versioning, performance, scheduler
- Pytest configuration with markers

✅ **CI/CD Pipeline** (`.github/workflows/ci_pipeline.yml`)
- Automated testing on push and PR
- Multi-version Python testing (3.9, 3.10, 3.11)
- Code coverage reporting with Codecov
- Linting with flake8, black, isort
- Dependency caching for faster builds
- Runs on Ubuntu latest

## Implementation Status

### Completed ✅

- **NDVI Satellite Data Integration**: Real MODIS NDVI data via Google Earth Engine (with synthetic fallback)
- **Caching System**: Full implementation with TTL and checksum validation
- **Incremental Updates**: Track and fetch only new data since last update
- **Quality Metrics**: Comprehensive data quality assessment and reporting
- **Data Versioning**: Version control with rollback capabilities
- **Performance Monitoring**: Profiling, timing, and optimization utilities
- **Automated Scheduling**: Periodic data refresh scheduling
- **Data Visualizations**: Charts, dashboards, and quality reports

### Current Limitations

1. **Processing modules**: Contain placeholder implementations (dry-run mode) - ready for production logic
2. **NDVI authentication**: Requires Google Earth Engine authentication for real satellite data (falls back to synthetic if not authenticated)
3. **Sequential execution**: Pipeline runs stages sequentially (no parallel processing yet)
4. **Memory usage**: Loads all data into memory (may need optimization for very large datasets)
5. **Error recovery**: Pipeline stops on first error (no partial recovery mechanism)

## Future Enhancements

- **Parallel ingestion and processing**: Concurrent execution using ThreadPoolExecutor
- **Distributed processing**: Support for very large datasets using Dask or Spark
- **Real-time streaming**: Live data ingestion and processing capabilities
- **Advanced anomaly detection**: ML-based anomaly detection algorithms
- **Production processing modules**: Implement real transformation logic (structure in place)
