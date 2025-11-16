# Project Organization

## Overview

This document describes the organizational structure of the Tanzania Climate Prediction project.

## Directory Structure

### Core Modules

```
modules/
├── ingestion/          # Data fetching from external sources
├── processing/         # Data transformation and feature creation
└── reporting/          # Output reporting utilities
```

### Scripts Organization

```
scripts/
├── analysis/           # Data analysis and EDA
│   ├── eda_analysis.py
│   ├── eda_master_dataset.py
│   ├── generate_visualizations.py
│   └── run_eda.py
│
├── demos/              # Testing individual modules
│   ├── demo_chirps_processing.py
│   ├── demo_chirps_synthetic.py
│   ├── demo_ndvi_synthetic.py
│   └── demo_ocean_indices_synthetic.py
│
├── reporting/          # Business metrics generation
│   ├── generate_business_reports.py
│   └── README.md
│
└── verification/       # Testing and validation
    ├── check_era5.py
    ├── fetch_real_data.py
    ├── test_gee_access.py
    └── verify_model_save_load.py
```

### Main Entry Points (Root)

```
root/
├── run_pipeline.py         # Data ingestion and processing
├── train_pipeline.py       # Model training
└── run_evaluation.py       # Model evaluation
```

**Why in root?**
- These are the primary entry points users interact with
- Keeps common commands simple: `python run_pipeline.py`
- Follows convention of main scripts in project root

### Reporting System

```
reporting/                          # Report generation modules
├── business_metrics.py            # Core reporting engine
└── visualize_business_metrics.py  # Visualization generator

scripts/reporting/                  # Report generation scripts
└── generate_business_reports.py   # Main report generator
```

**Separation rationale:**
- `reporting/` contains reusable modules (imported by other code)
- `scripts/reporting/` contains executable scripts (run directly)

## File Naming Conventions

### Scripts
- Use descriptive names: `generate_business_reports.py`
- Prefix with action verb: `run_`, `generate_`, `demo_`, `test_`
- Use underscores for multi-word names

### Modules
- Use noun-based names: `business_metrics.py`
- Group by functionality: `process_chirps.py`, `process_ndvi.py`
- Avoid redundant prefixes within directories

### Documentation
- Use UPPERCASE for major docs: `README.md`, `GUIDE.md`
- Use descriptive names: `BUSINESS_REPORTS_GUIDE.md`
- Keep in `docs/` directory

## Import Patterns

### From Root Scripts
```python
# Root scripts can import directly
from modules.ingestion import nasa_power_ingestion
from utils.logger import log_info
```

### From Nested Scripts
```python
# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Then import normally
from reporting.business_metrics import BusinessMetricsReporter
```

### From Modules
```python
# Modules use relative imports within their package
from .process_chirps import process_chirps_data

# Or absolute imports from project root
from utils.logger import log_info
```

## Output Organization

```
outputs/
├── processed/              # Processed datasets
│   ├── master_dataset.csv
│   └── features_*.csv
│
├── models/                 # Trained models
│   ├── random_forest_*.pkl
│   └── metadata files
│
├── evaluation/             # Model evaluation
│   ├── latest/            # Current evaluation
│   └── archive/           # Historical evaluations
│
├── experiments/            # Experiment tracking
│   └── experiment_log.jsonl
│
├── business_reports/       # Business metrics (gitignored)
│   ├── executive_summary.md
│   ├── *.csv
│   ├── *.json
│   └── visualizations/
│
└── visualizations/         # General visualizations
    ├── eda/
    └── models/
```

## Documentation Organization

```
docs/
├── README.md                      # Documentation index
├── BUSINESS_REPORTS_GUIDE.md      # Business reporting guide
├── MODEL_DEVELOPMENT_GUIDE.md     # ML pipeline guide
├── PROJECT_ORGANIZATION.md        # This file
├── pipeline_overview.md           # Pipeline architecture
├── IMPLEMENTATION_STATUS.md       # Project status
└── WEEK1_PROGRESS.md             # Weekly progress
```

## Configuration Files

```
root/
├── .env                    # Environment variables (gitignored)
├── .env.template          # Environment template
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── requirements-lock.txt  # Locked versions
├── pytest.ini            # Pytest configuration
├── pyproject.toml        # Project metadata
└── .flake8               # Linting configuration
```

## Best Practices

### Adding New Scripts

1. **Determine category:**
   - Analysis? → `scripts/analysis/`
   - Demo/test? → `scripts/demos/`
   - Reporting? → `scripts/reporting/`
   - Verification? → `scripts/verification/`

2. **Add documentation:**
   - Docstring at top of file
   - Usage examples in comments
   - Update relevant README

3. **Test from project root:**
   ```bash
   python scripts/category/your_script.py
   ```

### Adding New Modules

1. **Choose appropriate directory:**
   - Data fetching? → `modules/ingestion/`
   - Data processing? → `modules/processing/`
   - ML models? → `models/`
   - Utilities? → `utils/`

2. **Follow naming conventions:**
   - Use descriptive names
   - Match existing patterns
   - Add `__init__.py` if creating new package

3. **Add tests:**
   - Create corresponding test file in `tests/`
   - Follow naming: `test_your_module.py`

### Adding Documentation

1. **User-facing guides:**
   - Place in `docs/`
   - Use descriptive names
   - Link from main README

2. **Code documentation:**
   - Docstrings in modules
   - README in script directories
   - Inline comments for complex logic

## Migration Notes

### Recent Changes (2025-11-17)

**Moved:**
- `generate_business_reports.py` → `scripts/reporting/generate_business_reports.py`

**Added:**
- `scripts/README.md` - Scripts directory documentation
- `scripts/reporting/README.md` - Reporting scripts guide
- `docs/BUSINESS_REPORTS_GUIDE.md` - Business reporting documentation
- `docs/PROJECT_ORGANIZATION.md` - This file

**Updated:**
- Main `README.md` with business reports section
- Project structure documentation

### Backward Compatibility

Old command:
```bash
python generate_business_reports.py
```

New command:
```bash
python scripts/reporting/generate_business_reports.py
```

**Note:** Update any automation scripts or documentation that reference the old path.

## Future Organization

### Planned Improvements

1. **API Module:**
   - Create `api/` directory for REST API endpoints
   - Separate from core processing logic

2. **Deployment:**
   - Add `deployment/` for Docker, K8s configs
   - Infrastructure as code

3. **Notebooks:**
   - Add `notebooks/` for Jupyter notebooks
   - Exploratory analysis and demos

4. **Data:**
   - Keep `data/` gitignored
   - Document expected structure in README

## Questions?

For questions about project organization:
1. Check this document
2. Review `scripts/README.md` for script categories
3. Check individual directory READMEs
4. Refer to main project README

---

**Last Updated:** 2025-11-17
**Version:** 1.0
