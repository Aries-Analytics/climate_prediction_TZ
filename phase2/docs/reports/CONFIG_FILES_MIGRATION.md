# Configuration Files Migration Guide

## Current Config Files

### 1. Root Directory Config Files (Keep in Root)
These files should **STAY in root** - they're standard project configs:

```
Root Directory:
├── .env                    # Environment variables (KEEP IN ROOT)
├── .env.template           # Environment template (KEEP IN ROOT)
├── pyproject.toml          # Python project config (KEEP IN ROOT)
├── pytest.ini              # Pytest config (KEEP IN ROOT)
├── .flake8                 # Linting config (KEEP IN ROOT)
├── .gitignore              # Git ignore (KEEP IN ROOT)
├── requirements.txt        # Dependencies (KEEP IN ROOT)
└── requirements-lock.txt   # Locked dependencies (KEEP IN ROOT)
```

**Why keep in root?**
- Standard Python project convention
- Tools expect them in root directory
- No benefit to moving them

---

## 2. Application Config Files (Move to configs/)

### Current: Hardcoded in Python Files
Currently, configurations are hardcoded in Python files:

**models/model_config.py:**
- MODEL_CONFIG (Random Forest, XGBoost, LSTM, Ensemble hyperparameters)
- FEATURE_CONFIG (lag periods, rolling windows, etc.)
- TRAINING_CONFIG (train/val/test splits, cross-validation)

**Should be extracted to:**
```
configs/
├── model_config.yaml       # Model hyperparameters
├── feature_config.yaml     # Feature engineering settings
├── training_config.yaml    # Training parameters
└── pipeline_config.yaml    # Pipeline settings
```

---

## Recommended Config Structure

### configs/model_config.yaml
```yaml
# Model Hyperparameters Configuration

random_forest:
  n_estimators: 200
  max_depth: 15
  min_samples_split: 5
  min_samples_leaf: 2
  max_features: sqrt
  random_state: 42
  n_jobs: -1

xgboost:
  n_estimators: 200
  max_depth: 8
  learning_rate: 0.05
  subsample: 0.8
  colsample_bytree: 0.8
  random_state: 42
  n_jobs: -1

lstm:
  units: [128, 64]
  dropout: 0.2
  recurrent_dropout: 0.1
  epochs: 100
  batch_size: 16
  learning_rate: 0.001
  patience: 10
  sequence_length: 12

ensemble:
  weights:
    rf: 0.3
    xgb: 0.4
    lstm: 0.3
  method: weighted_average
```

### configs/feature_config.yaml
```yaml
# Feature Engineering Configuration

lag_periods: [1, 3, 6, 12]
rolling_windows: [3, 6]
rolling_stats: [mean, std]

interaction_features:
  - feature1: enso
    feature2: rainfall
    operation: multiply
  - feature1: iod
    feature2: ndvi
    operation: multiply

target_variables: [temperature, rainfall, ndvi]
max_missing_gap: 2
normalization_method: standardization
```

### configs/training_config.yaml
```yaml
# Training Configuration

data_splits:
  train: 0.70
  validation: 0.15
  test: 0.15

cross_validation:
  enabled: true
  folds: 5

early_stopping:
  enabled: true
  patience: 10

random_state: 42
shuffle: false  # Must be false for time series
```

### configs/pipeline_config.yaml
```yaml
# Pipeline Configuration

data_pipeline:
  input_path: outputs/processed/master_dataset.csv
  output_dir: outputs/data/processed
  log_level: INFO

model_pipeline:
  models_dir: outputs/models
  evaluation_dir: outputs/evaluation
  experiments_dir: outputs/experiments
  
data_sources:
  nasa_power:
    enabled: true
    start_year: 2000
    end_year: 2023
  
  era5:
    enabled: true
    start_year: 2000
    end_year: 2023
  
  chirps:
    enabled: true
    start_year: 2000
    end_year: 2023
  
  ndvi:
    enabled: true
    start_year: 2000
    end_year: 2023
  
  ocean_indices:
    enabled: true
    start_year: 2000
    end_year: 2023
```

---

## Migration Plan

### Phase 1: Create YAML Config Files (Optional - Future Enhancement)

**Step 1:** Create the YAML files in configs/
```bash
# Create config files
touch configs/model_config.yaml
touch configs/feature_config.yaml
touch configs/training_config.yaml
touch configs/pipeline_config.yaml
```

**Step 2:** Copy configurations from models/model_config.py to YAML files

**Step 3:** Update code to read from YAML instead of Python dict
```python
import yaml

def load_config(config_file):
    with open(f'configs/{config_file}', 'r') as f:
        return yaml.safe_load(f)

# Usage
model_config = load_config('model_config.yaml')
```

**Step 4:** Update models/model_config.py to load from YAML
```python
# Old way (current)
MODEL_CONFIG = {
    "random_forest": {...}
}

# New way (after migration)
import yaml
with open('configs/model_config.yaml') as f:
    MODEL_CONFIG = yaml.safe_load(f)
```

---

## Current Status

### What Exists Now
- ✅ configs/ directory created (empty)
- ✅ models/model_config.py with hardcoded configs
- ✅ Root config files (.env, pyproject.toml, etc.)

### What to Do

#### Option 1: Keep Current Setup (Recommended for Now)
**Pros:**
- Already working
- No code changes needed
- Simpler for development

**Cons:**
- Configs in Python code
- Need to edit code to change settings

**Recommendation:** Keep this for now, migrate later if needed

#### Option 2: Migrate to YAML (Future Enhancement)
**Pros:**
- Easier to modify configs
- No code changes to adjust settings
- More professional
- Better for production

**Cons:**
- Requires code changes
- Need to add PyYAML dependency
- More complexity

**Recommendation:** Do this in Phase 2 after testing current structure

---

## Summary

### Files That STAY in Root
```
.env                    # Environment variables
.env.template           # Environment template
pyproject.toml          # Python project config
pytest.ini              # Pytest config
.flake8                 # Linting config
.gitignore              # Git ignore
requirements.txt        # Dependencies
requirements-lock.txt   # Locked dependencies
README.md               # Main README
```

### Files That COULD Move to configs/ (Future)
```
models/model_config.py → configs/model_config.yaml
(extract configs)     → configs/feature_config.yaml
                      → configs/training_config.yaml
                      → configs/pipeline_config.yaml
```

### Current Recommendation
**Keep configs in models/model_config.py for now**
- It's working
- No breaking changes
- Can migrate to YAML later if needed

---

## Quick Answer to Your Question

**Where do config files move to?**

1. **Root config files (.env, pyproject.toml, etc.)** → **STAY IN ROOT** ✅
2. **Application configs (model settings, etc.)** → **Already in models/model_config.py** ✅
3. **Future YAML configs** → **configs/** (when we migrate)

**Current status:** configs/ directory is created and ready, but we're keeping the current Python-based configs in models/model_config.py for now. No migration needed yet!

---

## Next Steps

1. ✅ configs/ directory exists and is ready
2. ⏳ Keep using models/model_config.py (no changes needed)
3. ⏳ Optionally migrate to YAML in Phase 2 (future enhancement)

**No action needed right now - configs are fine where they are!** 🎯
