# Scripts Directory

Organized collection of utility scripts for the Tanzania Climate Prediction project.

## Directory Structure

```
scripts/
├── analysis/          # Data analysis and EDA scripts
├── demos/             # Demo scripts for testing individual modules
├── reporting/         # Business metrics and report generation
└── verification/      # Verification and testing utilities
```

## Quick Reference

### Analysis Scripts (`analysis/`)

- **`eda_analysis.py`** - Exploratory data analysis on processed data
- **`eda_master_dataset.py`** - EDA on merged master dataset
- **`generate_visualizations.py`** - Generate charts and plots
- **`run_eda.py`** - Main EDA runner

### Demo Scripts (`demos/`)

- **`demo_chirps_processing.py`** - Test CHIRPS rainfall processing
- **`demo_chirps_synthetic.py`** - Demo with synthetic CHIRPS data
- **`demo_ndvi_synthetic.py`** - Demo NDVI vegetation processing
- **`demo_ocean_indices_synthetic.py`** - Demo ocean indices processing

### Reporting Scripts (`reporting/`)

- **`generate_business_reports.py`** - Generate all business metrics reports
  - Insurance triggers, alerts, financial impact
  - Visualizations and dashboards

### Verification Scripts (`verification/`)

- **`check_era5.py`** - Verify ERA5 data access
- **`fetch_real_data.py`** - Test real data fetching
- **`test_gee_access.py`** - Test Google Earth Engine access
- **`verify_model_save_load.py`** - Test model serialization

## Main Entry Points (Root Directory)

These scripts remain in the project root as main entry points:

- **`run_pipeline.py`** - Run the full data ingestion and processing pipeline
- **`train_pipeline.py`** - Train ML models
- **`run_evaluation.py`** - Evaluate trained models

## Usage Examples

### Generate Business Reports
```bash
python scripts/reporting/generate_business_reports.py
```

### Run EDA
```bash
python scripts/analysis/run_eda.py
```

### Test CHIRPS Processing
```bash
python scripts/demos/demo_chirps_processing.py
```

### Verify Model Functionality
```bash
python scripts/verification/verify_model_save_load.py
```

## Adding New Scripts

When adding new scripts, place them in the appropriate subdirectory:

- **Analysis**: Data exploration, statistics, visualizations
- **Demos**: Testing individual modules with sample data
- **Reporting**: Business metrics, reports, dashboards
- **Verification**: Testing, validation, access checks

## Notes

- All scripts should be runnable from the project root
- Use relative imports from project root
- Add `sys.path` adjustments if needed for imports
- Document usage in script docstrings
