# Project Structure

## Root Directory Organization

The project root has been cleaned up. Files are now organized as follows:

### Configuration Files (Root)
```
.env                    # Environment variables (not in git)
.env.template           # Template for environment variables
.flake8                 # Python linting configuration
.gitignore              # Git ignore patterns
docker-compose.dev.yml  # Docker compose for development
docker-compose.prod.yml # Docker compose for production
pyproject.toml          # Python project metadata
pytest.ini              # Pytest configuration
README.md               # Main project documentation
requirements.txt        # Python dependencies
requirements-lock.txt   # Locked dependency versions
```

### Directory Structure

```
.
├── backend/                    # Backend API and services
│   ├── app/                   # FastAPI application
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core configuration
│   │   ├── models/           # Database models
│   │   └── services/         # Business logic
│   │       └── pipeline/     # Pipeline orchestration
│   ├── scripts/              # Backend utility scripts
│   ├── tests/                # Backend tests
│   └── alembic/              # Database migrations
│
├── frontend/                   # React frontend application
│   ├── src/                  # Source code
│   └── public/               # Static assets
│
├── modules/                    # Data processing modules
│   ├── ingestion/            # Data ingestion (CHIRPS, NASA, ERA5, etc.)
│   ├── processing/           # Data processing
│   └── calibration/          # Model calibration
│
├── pipelines/                  # Pipeline scripts
│   ├── run_pipeline.py       # Main pipeline runner
│   └── train_pipeline.py     # Model training pipeline
│
├── scripts/                    # Utility scripts
│   ├── analyze_2021_gap.py   # Analysis scripts
│   ├── check_2021_gap.py     # Data validation
│   ├── setup_dashboard.sh    # Dashboard setup
│   └── commit_changes.bat    # Git helper
│
├── evaluation/                 # Model evaluation
│   ├── evaluate.py           # Evaluation logic
│   └── run_evaluation.py     # Evaluation runner
│
├── docs/                       # Documentation
│   ├── README.md             # Documentation index
│   ├── pipeline_overview.md  # Pipeline documentation
│   ├── FORECAST_GENERATION_SUMMARY.md
│   ├── RECOMMENDATIONS_FIX_SUMMARY.md
│   ├── INGESTION_UPDATE_SUMMARY.md
│   └── PROJECT_STRUCTURE.md  # This file
│
├── tests/                      # Root-level tests
├── utils/                      # Shared utilities
├── configs/                    # Configuration files
├── data/                       # Data storage
│   ├── raw/                  # Raw data
│   ├── processed/            # Processed data
│   └── interim/              # Intermediate data
│
├── models/                     # Trained models
├── outputs/                    # Pipeline outputs
├── logs/                       # Application logs
├── dashboard/                  # Dashboard application
├── preprocessing/              # Data preprocessing
└── reporting/                  # Report generation
```

## Key Directories Explained

### Backend (`backend/`)
Contains the FastAPI backend application with:
- REST API endpoints
- Database models and migrations
- Pipeline orchestration services
- Business logic and services

### Modules (`modules/`)
Reusable data processing modules:
- **ingestion/**: Fetch data from external sources (CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices)
- **processing/**: Transform and clean data
- **calibration/**: Model calibration and threshold optimization

### Pipelines (`pipelines/`)
Main pipeline execution scripts:
- **run_pipeline.py**: Execute the full data pipeline
- **train_pipeline.py**: Train ML models

### Scripts (`scripts/`)
Utility and helper scripts:
- Data analysis scripts
- Setup and installation scripts
- Maintenance scripts

### Evaluation (`evaluation/`)
Model evaluation and performance analysis:
- Evaluation metrics
- Performance reports
- Validation scripts

### Docs (`docs/`)
Project documentation:
- Architecture documentation
- Implementation guides
- API documentation
- Summary reports

## File Organization Rules

### Root Directory
**Keep in root:**
- Configuration files (.env, .gitignore, etc.)
- Docker compose files
- Package configuration (pyproject.toml, requirements.txt)
- Main README.md

**Move to subdirectories:**
- Python scripts → `scripts/` or `pipelines/`
- Documentation → `docs/`
- Tests → `tests/` or `backend/tests/`

### Scripts vs Pipelines
- **scripts/**: One-off utilities, analysis, setup
- **pipelines/**: Repeatable data/ML pipelines

### Backend vs Modules
- **backend/**: API, database, orchestration
- **modules/**: Reusable data processing logic

## Running the Organization Script

To organize files automatically:

```bash
python organize_root.py
```

This will move files from root to their appropriate directories.

## Maintenance

When adding new files:
1. **Scripts**: Place in `scripts/` or `pipelines/`
2. **Documentation**: Place in `docs/`
3. **Tests**: Place in `tests/` or `backend/tests/`
4. **Configuration**: Keep in root only if project-wide

Keep the root directory clean and organized!
