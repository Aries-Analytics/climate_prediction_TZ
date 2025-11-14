# Pipeline Run Instructions

## Prerequisites

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for ERA5 processing)
- 10GB free disk space (for CHIRPS NetCDF files)
- Internet connection (for data ingestion)

### Required Python Packages

```bash
pip install pandas requests xarray netCDF4 cdsapi python-dotenv pyarrow earthengine-api
```

Or install from requirements file:
```bash
pip install -r requirements.txt
```

**Note:** `earthengine-api` is optional but recommended for real NDVI satellite data. Without it, the pipeline will use synthetic NDVI data.

### Environment Setup

1. **Create `.env` file** in project root:

```bash
# NASA POWER API
NASA_API_URL=https://power.larc.nasa.gov/api/temporal/monthly/point

# ERA5 CDS API (get from https://cds.climate.copernicus.eu/user)
ERA5_API_KEY=your_uid:your_api_key

# CHIRPS Data Portal
CHIRPS_BASE_URL=https://data.chc.ucsb.edu/products/CHIRPS-2.0

# Ocean Indices
OCEAN_INDICES_SOURCE=https://psl.noaa.gov/data/climateindices/list/

# Project Settings
DEFAULT_REGION=Tanzania
DEFAULT_CRS=EPSG:4326
```

2. **Configure ERA5 CDS API** (required for ERA5 data):

Create `~/.cdsapirc` file:
```
url: https://cds.climate.copernicus.eu/api/v2
key: {UID}:{API-KEY}
```

Get your credentials:
- Register at https://cds.climate.copernicus.eu/user/register
- Login and go to https://cds.climate.copernicus.eu/user
- Copy your UID and API key

3. **Configure Google Earth Engine** (optional, for real NDVI satellite data):

```bash
# Install Earth Engine API
pip install earthengine-api

# Authenticate (one-time setup)
earthengine authenticate
```

This opens a browser for Google authentication. Follow the prompts to authorize.

**Benefits of GEE setup:**
- Real MODIS satellite NDVI data (1km resolution)
- Actual vegetation measurements from 2000-present
- Captures real drought events and anomalies

**Without GEE:**
- Pipeline automatically uses synthetic NDVI data
- Based on climatological patterns
- Good for testing and development

See `docs/GEE_SETUP.md` for detailed setup instructions and troubleshooting.

---

## Running the Pipeline

### Quick Start

```bash
# Run in debug mode (fast, uses mock data)
python run_pipeline.py --debug

# Run in production mode (real data ingestion)
python run_pipeline.py
```

### Debug Mode (Recommended for Testing)

```bash
python run_pipeline.py --debug
```

**What it does:**
- Uses mock data (no real API calls)
- Fast execution (< 1 minute)
- Verbose logging (DEBUG level)
- Good for testing pipeline logic

**Output:**
- Placeholder processed files in `outputs/processed/`
- Master dataset with mock data
- Detailed logs in `logs/pipeline_YYYY-MM-DD.log`

### Production Mode

```bash
python run_pipeline.py
```

**What it does:**
- Fetches real data from external APIs
- Full data processing
- Standard logging (INFO level)
- Takes 10-30 minutes depending on network speed

**Output:**
- Raw data in `data/raw/`
- Processed data in `outputs/processed/`
- Master dataset: `outputs/processed/master_dataset.csv` and `.parquet`
- Logs in `logs/pipeline_YYYY-MM-DD.log`

---

## Running Individual Modules

### Ingestion Only

```python
from modules.ingestion import nasa_power_ingestion

# Fetch NASA POWER data
df = nasa_power_ingestion.fetch_data(
    dry_run=False,
    start_year=2020,
    end_year=2023
)

print(f"Fetched {len(df)} records")
```

### Processing Only

```python
from modules.processing import process_nasa_power
import pandas as pd

# Load raw data
raw_data = pd.read_csv('data/raw/nasa_power_raw.csv')

# Process it
processed_data = process_nasa_power.process(raw_data)
```

### Merge Only

```python
from modules.processing.merge_processed import merge_all

# Merge all processed files
master_df = merge_all()
print(f"Master dataset has {len(master_df)} rows")
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_pipeline.py
pytest tests/test_merge_processed.py
```

### Run with Verbose Output

```bash
pytest -v tests/
```

### Run with Coverage

```bash
pytest --cov=modules --cov=utils tests/
```

---

## CI/CD Workflows

### GitHub Actions

The project includes a comprehensive CI/CD pipeline in `.github/workflows/ci_pipeline.yml`

#### CI Pipeline Workflow

**File:** `.github/workflows/ci_pipeline.yml`

**Triggers:**
- Push to `main` or `phase2/feature-expansion` branches
- Pull requests to `main` branch

**Jobs:**

##### 1. Test Job

**Matrix Strategy:** Tests across Python 3.9, 3.10, and 3.11

**Steps:**
1. Checkout code
2. Setup Python (matrix version)
3. Cache pip dependencies
4. Install dependencies from requirements.txt
5. Create necessary directories (outputs/processed, logs)
6. Run pytest with coverage
7. Upload coverage reports to Codecov

**Coverage:**
- Modules: `modules/` and `utils/`
- Reports: XML and terminal output
- Integration: Codecov for tracking

##### 2. Lint Job

**Steps:**
1. Checkout code
2. Setup Python 3.10
3. Install linting tools (flake8, black, isort)
4. Run flake8 (max line length: 120)
5. Check code formatting with black
6. Check import sorting with isort

**Note:** Linting steps continue on error (non-blocking)

#### Running CI Checks Locally

**Run all tests:**
```bash
pytest tests/ -v --cov=modules --cov=utils --cov-report=xml --cov-report=term
```

**Run linting:**
```bash
# Flake8
flake8 modules/ utils/ tests/ --max-line-length=120 --extend-ignore=E203,W503

# Black formatting check
black --check modules/ utils/ tests/ --line-length=120

# Black auto-format
black modules/ utils/ tests/ --line-length=120

# isort check
isort --check-only modules/ utils/ tests/ --profile black

# isort auto-fix
isort modules/ utils/ tests/ --profile black
```

**Run locally with act (GitHub Actions simulator):**
```bash
# Install act: https://github.com/nektos/act
# Windows: choco install act-cli
# Mac: brew install act
# Linux: See GitHub releases

# Run all workflows
act push

# Run specific job
act -j test
act -j lint
```

#### CI/CD Features

✅ **Multi-version testing**: Python 3.9, 3.10, 3.11  
✅ **Dependency caching**: Faster builds with pip cache  
✅ **Code coverage**: Automated coverage tracking  
✅ **Code quality**: Automated linting and formatting checks  
✅ **Non-blocking lints**: Linting failures don't block PRs  
✅ **Branch protection**: Runs on main and feature branches

---

## Troubleshooting

### Common Issues

#### 1. ERA5 Authentication Error

**Error:** `Exception: Missing/incomplete configuration file`

**Solution:**
```bash
# Create ~/.cdsapirc with your credentials
echo "url: https://cds.climate.copernicus.eu/api/v2" > ~/.cdsapirc
echo "key: YOUR_UID:YOUR_API_KEY" >> ~/.cdsapirc
```

#### 2. Missing Dependencies

**Error:** `ImportError: No module named 'xarray'`

**Solution:**
```bash
pip install xarray netCDF4
```

#### 3. CHIRPS Download Timeout

**Error:** `requests.exceptions.Timeout`

**Solution:**
- Check internet connection
- Retry (CHIRPS files are large, ~1-2GB per year)
- Reduce date range to fewer years

#### 4. No Processed Files Found

**Error:** `FileNotFoundError: No processed files found`

**Solution:**
- Run ingestion and processing stages first
- Check `outputs/processed/` directory exists
- Verify processing modules completed successfully

#### 5. Memory Error

**Error:** `MemoryError`

**Solution:**
- Reduce date range (fewer years)
- Process data sources individually
- Increase system RAM

### Checking Logs

View the latest log file:
```bash
# Linux/Mac
tail -f logs/pipeline_$(date +%Y-%m-%d).log

# Windows
Get-Content logs\pipeline_$(Get-Date -Format yyyy-MM-dd).log -Tail 50 -Wait
```

View all errors:
```bash
# Linux/Mac
grep ERROR logs/pipeline_*.log

# Windows
Select-String -Path logs\pipeline_*.log -Pattern "ERROR"
```

### Validating Output

Check master dataset:
```python
import pandas as pd

# Load master dataset
df = pd.read_csv('outputs/processed/master_dataset.csv')

# Basic checks
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Missing values:\n{df.isnull().sum()}")
print(f"\nFirst few rows:\n{df.head()}")
```

---

## Performance Optimization

### Reduce Execution Time

1. **Use debug mode for testing:**
   ```bash
   python run_pipeline.py --debug
   ```

2. **Reduce date range:**
   ```python
   # In ingestion modules
   fetch_data(start_year=2020, end_year=2023)  # Only 4 years
   ```

3. **Skip slow sources:**
   ```python
   # Comment out in run_pipeline.py
   # ("ERA5", era5_ingestion.fetch_data),
   # ("CHIRPS", chirps_ingestion.fetch_data),
   ```

### Reduce Memory Usage

1. **Process sources individually:**
   ```python
   # Instead of running full pipeline
   # Process one source at a time
   ```

2. **Use Parquet format:**
   ```python
   # More memory efficient than CSV
   df = pd.read_parquet('outputs/processed/master_dataset.parquet')
   ```

3. **Clear intermediate data:**
   ```python
   # After processing
   del raw_data
   import gc
   gc.collect()
   ```

---

## Using Advanced Features

### Caching

Enable caching to avoid redundant API calls:

```python
from utils.cache import get_cache
from modules.ingestion import nasa_power_ingestion

cache = get_cache(default_ttl_hours=24)

# Try to get from cache first
params = {'start_year': 2020, 'end_year': 2023}
df = cache.get('nasa_power', params)

if df is None:
    # Cache miss - fetch from API
    df = nasa_power_ingestion.fetch_data(**params)
    cache.set('nasa_power', params, df)
```

### Incremental Updates

Fetch only new data since last update:

```python
from utils.incremental import get_tracker
from modules.ingestion import nasa_power_ingestion

tracker = get_tracker()

# Get incremental range
start_year, start_month, end_year, end_month, is_incremental = \
    tracker.get_incremental_range('nasa_power', 2010, 2023)

if start_year is not None:
    # Fetch only new data
    new_data = nasa_power_ingestion.fetch_data(
        start_year=start_year,
        end_year=end_year
    )
    
    # Merge with existing data
    merged_data = tracker.merge_with_existing('nasa_power', new_data)
    
    # Record the update
    tracker.record_update('nasa_power', end_year, 12, len(new_data))
```

### Quality Metrics

Assess data quality:

```python
from utils.quality_metrics import get_quality_metrics
import pandas as pd

qm = get_quality_metrics()

# Load data
df = pd.read_csv('data/raw/nasa_power_raw.csv')

# Calculate metrics
metrics = qm.calculate_metrics(
    df, 
    'nasa_power',
    expected_columns=['year', 'month', 't2m', 'prectotcorr']
)

# Generate report
report = qm.generate_report(metrics)
print(report)

# Save metrics
qm.save_metrics(metrics, 'nasa_power')
```

### Data Versioning

Version control for datasets:

```python
from utils.versioning import get_version_control

vc = get_version_control()

# Create a new version
version = vc.create_version(
    'nasa_power',
    'data/raw/nasa_power_raw.csv',
    description='Updated with 2023 data',
    tags=['2023', 'complete']
)

# List versions
versions = vc.list_versions('nasa_power')
for v in versions:
    print(f"Version {v['version']}: {v['description']}")

# Rollback to previous version
vc.rollback('nasa_power', version=2, target_path='data/raw/nasa_power_raw.csv')
```

### Performance Monitoring

Track pipeline performance:

```python
from utils.performance import get_performance_monitor, timer

monitor = get_performance_monitor()

# Use decorator for automatic timing
@timer
def my_function():
    # Your code here
    pass

# Manual recording
import time
start = time.time()
# ... do work ...
duration = time.time() - start
monitor.record_metric('my_operation', duration, rows_processed=1000)

# Save metrics
monitor.save_metrics()

# Get summary
summary = monitor.get_summary('my_operation')
print(f"Average duration: {summary['avg_duration']:.2f}s")
```

### Automated Scheduling

Schedule periodic data refreshes:

```python
from utils.scheduler import get_scheduler, create_data_refresh_job
from modules.ingestion import nasa_power_ingestion

scheduler = get_scheduler()

# Create a refresh job
job = create_data_refresh_job(
    'nasa_power',
    nasa_power_ingestion.fetch_data,
    dry_run=False,
    start_year=2020,
    end_year=2023
)

# Schedule daily at 2 AM
scheduler.schedule_job(
    'nasa_power_daily',
    job,
    schedule_type='daily',
    schedule_time='02:00'
)

# Start the scheduler
scheduler.start()

# List scheduled jobs
jobs = scheduler.list_jobs()
for name, info in jobs.items():
    print(f"{name}: {info['next_run']}")
```

### Data Visualization

Generate visualizations:

```python
from utils.visualizations import get_visualizer
import pandas as pd

viz = get_visualizer()

# Load data
df = pd.read_csv('data/raw/nasa_power_raw.csv')

# Time series plot
viz.plot_time_series(
    df,
    value_col='t2m',
    title='Temperature Over Time',
    ylabel='Temperature (°C)',
    save_name='temperature_timeseries.png'
)

# Quality metrics dashboard
from utils.quality_metrics import get_quality_metrics
qm = get_quality_metrics()
metrics = qm.calculate_metrics(df, 'nasa_power')
viz.plot_quality_metrics(metrics, save_name='quality_dashboard.png')

# Correlation matrix
viz.plot_correlation_matrix(df, save_name='correlation_matrix.png')
```

---

## Advanced Usage

### Custom Date Range

```python
from run_pipeline import run_pipeline
from modules.ingestion import nasa_power_ingestion

# Modify ingestion call
df = nasa_power_ingestion.fetch_data(
    dry_run=False,
    start_year=2015,
    end_year=2020
)
```

### Custom Region

```python
# Modify bounds in ingestion modules
custom_bounds = {
    "north": -5.0,
    "south": -8.0,
    "west": 33.0,
    "east": 36.0
}

df = chirps_ingestion.fetch_data(
    bounds=custom_bounds,
    start_year=2020,
    end_year=2023
)
```

### Parallel Processing (Future)

```python
# Not yet implemented
# Future enhancement for faster execution
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(module.fetch_data)
        for module in ingestion_modules
    ]
```

---

## Output Files

### Expected Output Structure

```
outputs/processed/
├── nasa_power_processed.csv
├── era5_processed.csv
├── chirps_processed.csv
├── ndvi_processed.csv
├── ocean_indices_processed.csv
├── master_dataset.csv
└── master_dataset.parquet
```

### File Sizes (Approximate)

| File | Size (2010-2023) |
|------|------------------|
| nasa_power_processed.csv | < 1 MB |
| era5_processed.csv | < 1 MB |
| chirps_processed.csv | < 1 MB |
| ndvi_processed.csv | < 1 MB |
| ocean_indices_processed.csv | < 1 MB |
| master_dataset.csv | 1-5 MB |
| master_dataset.parquet | 0.5-2 MB |

---

## Scheduling Automated Runs

### Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/phase2 && /path/to/python run_pipeline.py >> logs/cron.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `run_pipeline.py`
   - Start in: `C:\path\to\phase2`

### Using Python Script

```python
# scheduled_run.py
import schedule
import time
from run_pipeline import run_pipeline

def job():
    print("Starting scheduled pipeline run...")
    run_pipeline(debug=False)

# Run every day at 2 AM
schedule.every().day.at("02:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Getting Help

### Check Documentation

- `docs/pipeline_overview.md` - Architecture and design
- `docs/data_dictionary.md` - Data schemas
- `docs/feature_engineering.md` - Feature engineering guide

### Check Logs

- `logs/pipeline_YYYY-MM-DD.log` - Daily execution logs

### Debug Mode

- Run with `--debug` flag for verbose output
- Check each stage completes successfully

### Contact

- Open an issue on GitHub
- Check existing issues for similar problems
- Review error messages and stack traces in logs
