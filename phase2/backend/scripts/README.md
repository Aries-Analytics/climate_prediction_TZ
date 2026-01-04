# Dashboard Data Loading Scripts

This directory contains scripts for loading data from the ML pipeline into the dashboard database.

## Overview

The data loading process consists of several steps:

1. **Climate Data**: Load processed climate data from `master_dataset.csv`
2. **Trigger Events**: Extract and load drought, flood, and crop failure triggers
3. **Model Metrics**: Load ML model performance metrics
4. **Users**: Seed initial user accounts (admin, analyst, viewer)

## Prerequisites

1. **Database Running**: Ensure PostgreSQL is running (via Docker Compose)
2. **Pipeline Data**: Run the ML pipeline to generate data files:
   ```bash
   python run_pipeline.py
   python train_pipeline.py
   ```

## Quick Start

### Load All Data (Recommended)

```bash
cd backend
python scripts/load_all_data.py --clear
```

This will:
- Clear existing data
- Load climate data (191 records from 2010-2025)
- Load trigger events (67 events)
- Load model metrics (4 models)

### Seed Users

```bash
python scripts/seed_users.py
```

Creates three default users:
- **admin** / admin123 (full access)
- **analyst** / analyst123 (read/write)
- **viewer** / viewer123 (read-only)

⚠️ **Change these passwords in production!**

### Verify Data

```bash
python scripts/verify_data.py
```

Checks that all data loaded correctly.

## Individual Scripts

### 1. Load Climate Data

```bash
python scripts/load_climate_data.py [--csv PATH] [--clear]
```

**Options:**
- `--csv`: Path to master_dataset.csv (default: `outputs/processed/master_dataset.csv`)
- `--clear`: Clear existing data before loading

**Example:**
```bash
python scripts/load_climate_data.py --clear
```

### 2. Load Trigger Events

```bash
python scripts/load_trigger_events.py [--csv PATH] [--clear]
```

**Options:**
- `--csv`: Path to master CSV (default: `outputs/processed/master_dataset.csv`)
- `--clear`: Clear existing data before loading

**Example:**
```bash
python scripts/load_trigger_events.py --clear
```

### 3. Load Model Metrics

```bash
python scripts/load_model_metrics.py [--results PATH] [--clear]
```

**Options:**
- `--results`: Path to training_results.json (default: `outputs/models/training_results.json`)
- `--clear`: Clear existing data before loading

**Example:**
```bash
python scripts/load_model_metrics.py --clear
```

### 4. Master Loader (All Data)

```bash
python scripts/load_all_data.py [--clear] [--skip-models]
```

**Options:**
- `--clear`: Clear all existing data before loading
- `--skip-models`: Skip loading model metrics
- `--verify-only`: Only verify data, don't load (not yet implemented)

**Examples:**
```bash
# Load all data (keep existing)
python scripts/load_all_data.py

# Clear and reload all data
python scripts/load_all_data.py --clear

# Load only climate and trigger data
python scripts/load_all_data.py --skip-models
```

### 5. Seed Users

```bash
python scripts/seed_users.py
```

Creates initial user accounts. Safe to run multiple times (won't create duplicates).

### 6. Verify Data

```bash
python scripts/verify_data.py
```

Runs verification checks on all loaded data.

## Typical Workflow

### First Time Setup

```bash
# 1. Start database
cd dashboard
docker-compose -f docker-compose.dev.yml up -d db

# 2. Run migrations (if needed)
cd backend
alembic upgrade head

# 3. Load all data
python scripts/load_all_data.py --clear

# 4. Seed users
python scripts/seed_users.py

# 5. Verify everything
python scripts/verify_data.py

# 6. Start backend and frontend
cd ..
docker-compose -f docker-compose.dev.yml up
```

### Reload Data (After Pipeline Re-run)

```bash
# Just reload data (keeps users)
python scripts/load_all_data.py --clear
python scripts/verify_data.py
```

## Troubleshooting

### Database Connection Error

**Error:** `could not connect to server`

**Solution:**
```bash
# Check if database is running
docker-compose -f docker-compose.dev.yml ps

# Start database if not running
docker-compose -f docker-compose.dev.yml up -d db

# Wait a few seconds for database to be ready
```

### Missing Data Files

**Error:** `FileNotFoundError: outputs/processed/master_dataset.csv`

**Solution:**
```bash
# Run the data pipeline first
python run_pipeline.py
python train_pipeline.py
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Run scripts from backend directory
python scripts/load_all_data.py
```

### Duplicate Key Errors

**Error:** `IntegrityError: duplicate key value`

**Solution:**
```bash
# Use --clear flag to remove existing data first
python scripts/load_all_data.py --clear
```

## Data Verification Checklist

After loading, verify:

- [ ] Climate data: 191 records (2010-01 to 2025-11)
- [ ] Trigger events: Multiple records (varies by data)
- [ ] Model metrics: 4 records (RF, XGBoost, LSTM, Ensemble)
- [ ] Users: 3 records (admin, analyst, viewer)

Run `python scripts/verify_data.py` to check all of these automatically.

## Notes

- **Data Persistence**: Data is stored in PostgreSQL and persists across container restarts
- **Idempotency**: Scripts can be run multiple times safely (use `--clear` to reset)
- **Performance**: Loading 72 climate records takes ~1-2 seconds
- **Batch Size**: Scripts use batch inserts (100 records) for efficiency

## Next Steps

After loading data:

1. **Start Services**: `docker-compose -f docker-compose.dev.yml up`
2. **Access Dashboard**: http://localhost:3000
3. **Login**: Use admin/admin123 (or other seeded credentials)
4. **Verify Dashboards**: Check that all dashboards display real data

## Support

For issues:
1. Check logs: `docker-compose -f docker-compose.dev.yml logs backend`
2. Verify data: `python scripts/verify_data.py`
3. Check database: `docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d climate_dashboard`
