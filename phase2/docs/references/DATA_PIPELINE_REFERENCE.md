# Data Pipeline Reference

**Last Updated**: January 4, 2026  
**Version**: 2.0  
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
- Coordinates ingestion and forecasting stages
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
**Coverage**: Global ocean-atmosphere patterns

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
- `outputs/processed/master_dataset.csv`
- `outputs/processed/master_dataset.parquet`
- Merge metadata and quality reports

---

## Automated Pipeline System

### Scheduling

**Scheduler**: APScheduler with persistent job store  
**Default Schedule**: Daily at 06:00 UTC  
**Configuration**: Environment variable `PIPELINE_SCHEDULE`

**Schedule Examples**:
```bash
# Daily at 6 AM UTC
PIPELINE_SCHEDULE="0 6 * * *"

# Twice daily (6 AM and 6 PM UTC)
PIPELINE_SCHEDULE="0 6,18 * * *"

# Weekly on Sundays at 2 AM UTC
PIPELINE_SCHEDULE="0 2 * * 0"
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
PIPELINE_TIMEZONE=UTC
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

## Related Documentation

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Quick start guide
- **[ML_MODEL_REFERENCE.md](./ML_MODEL_REFERENCE.md)** - ML model details
- **[TESTING_REFERENCE.md](./TESTING_REFERENCE.md)** - Testing documentation
- **[DEPLOYMENT_REFERENCE.md](./DEPLOYMENT_REFERENCE.md)** - Deployment guide
- **[data_dictionary.md](./data_dictionary.md)** - Data schemas

---

**Document Version**: 2.0  
**Last Updated**: January 4, 2026  
**Status**: ✅ Production Ready  
**Consolidates**: pipeline_overview.md, AUTOMATED_PIPELINE_GUIDE.md, PIPELINE_EXECUTION_SUMMARY.md, PIPELINE_REPLACEMENT_COMPLETE.md, PIPELINE_REPLACEMENT_SUMMARY.md, PIPELINE_RUN_SUMMARY_2010_2025.md