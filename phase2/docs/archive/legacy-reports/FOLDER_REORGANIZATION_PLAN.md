# 📁 Folder Reorganization Plan
**Purpose:** Make the project more organized and easier to navigate

---

## 🔴 Current Issues

### 1. **Root Directory Clutter** (30+ files!)
- Too many Python scripts in root
- Too many markdown documentation files in root
- Mix of demo scripts, test scripts, and main scripts
- Hard to find what you need

### 2. **Duplicate/Similar Folders**
- `data_pipeline/` vs `modules/` (both have ingestion)
- `preprocessing/` vs `feature_engineering/` (similar purpose)
- `model_pipeline/` vs `models/` (confusing separation)
- `evaluation/` folder at root (should be in models or outputs)

### 3. **Documentation Scattered**
- 15+ markdown files in root directory
- Some docs in `docs/` folder
- Hard to find the right documentation

### 4. **Test Files Mixed**
- Test scripts in root directory
- Some tests in `tests/` folder
- Demo scripts mixed with real scripts

---

## ✅ Proposed New Structure

```
tanzania-climate-prediction/
│
├── 📂 src/                          # All source code
│   ├── ingestion/                   # Data ingestion (merge data_pipeline + modules/ingestion)
│   │   ├── __init__.py
│   │   ├── nasa_power_ingestion.py
│   │   ├── era5_ingestion.py
│   │   ├── chirps_ingestion.py
│   │   ├── ndvi_ingestion.py
│   │   └── ocean_indices_ingestion.py
│   │
│   ├── processing/                  # Data processing (merge preprocessing + modules/processing)
│   │   ├── __init__.py
│   │   ├── process_nasa_power.py
│   │   ├── process_era5.py
│   │   ├── process_chirps.py
│   │   ├── process_ndvi.py
│   │   ├── process_ocean_indices.py
│   │   └── merge_processed.py
│   │
│   ├── features/                    # Feature engineering
│   │   ├── __init__.py
│   │   └── engineer_features.py
│   │
│   ├── models/                      # ML models
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── random_forest_model.py
│   │   ├── xgboost_model.py
│   │   ├── lstm_model.py
│   │   ├── ensemble_model.py
│   │   ├── model_config.py
│   │   ├── model_trainer.py
│   │   └── experiment_tracking.py
│   │
│   ├── evaluation/                  # Model evaluation
│   │   ├── __init__.py
│   │   └── evaluate.py
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── config.py
│       ├── validation.py
│       └── validator.py
│
├── 📂 pipelines/                    # Main pipeline scripts
│   ├── run_data_pipeline.py        # Data ingestion + processing
│   ├── run_model_pipeline.py       # Model training + evaluation
│   └── run_full_pipeline.py        # End-to-end pipeline
│
├── 📂 scripts/                      # Utility scripts
│   ├── demos/                       # Demo scripts
│   │   ├── demo_chirps_processing.py
│   │   ├── demo_chirps_synthetic.py
│   │   ├── demo_ndvi_synthetic.py
│   │   └── demo_ocean_indices_synthetic.py
│   │
│   ├── analysis/                    # Analysis scripts
│   │   ├── eda_analysis.py
│   │   ├── eda_master_dataset.py
│   │   ├── run_eda.py
│   │   └── generate_visualizations.py
│   │
│   └── verification/                # Verification scripts
│       ├── check_era5.py
│       ├── test_gee_access.py
│       ├── verify_model_save_load.py
│       └── fetch_real_data.py
│
├── 📂 tests/                        # All tests
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_evaluation_report.py
│   ├── test_experiment_tracking.py
│   ├── test_seasonal_evaluation.py
│   ├── test_visualizations.py
│   └── test_merge_processed.py
│
├── 📂 outputs/                      # All outputs (organized by date)
│   ├── data/                        # Processed data
│   │   ├── raw/                     # Raw ingested data
│   │   └── processed/               # Processed data
│   │
│   ├── models/                      # Trained models
│   │   ├── YYYY-MM-DD/              # Models by date
│   │   └── production/              # Production models
│   │
│   ├── evaluation/                  # Evaluation reports
│   │   ├── YYYY-MM-DD/              # Reports by date
│   │   └── latest/                  # Latest reports (symlink)
│   │
│   ├── experiments/                 # Experiment tracking
│   │   └── experiment_log.jsonl
│   │
│   └── visualizations/              # All visualizations
│       ├── eda/                     # EDA plots
│       └── models/                  # Model plots
│
├── 📂 docs/                         # All documentation
│   ├── 📂 guides/                   # User guides
│   │   ├── QUICK_START.md
│   │   ├── DATA_PIPELINE_GUIDE.md
│   │   ├── MODEL_PIPELINE_GUIDE.md
│   │   └── EVALUATION_GUIDE.md
│   │
│   ├── 📂 reports/                  # Status reports
│   │   ├── PIPELINE_STATUS.md
│   │   ├── MODEL_STATUS.md
│   │   └── EVALUATION_RESULTS.md
│   │
│   ├── 📂 specs/                    # Technical specs (move from .kiro)
│   │   ├── data-ingestion/
│   │   ├── ml-model-development/
│   │   └── ci-cd-pipeline-fixes/
│   │
│   ├── 📂 api/                      # API documentation
│   │   ├── data_sources.md
│   │   └── model_api.md
│   │
│   ├── README.md                    # Main documentation
│   ├── ARCHITECTURE.md              # System architecture
│   └── CHANGELOG.md                 # Version history
│
├── 📂 configs/                      # Configuration files
│   ├── model_config.yaml
│   ├── data_config.yaml
│   └── pipeline_config.yaml
│
├── 📂 logs/                         # Log files
│   └── pipeline_YYYY-MM-DD.log
│
├── 📂 .github/                      # GitHub configs
│   └── workflows/
│
├── 📂 .kiro/                        # Kiro IDE configs
│   ├── settings/
│   └── steering/
│
├── .env                             # Environment variables
├── .env.template                    # Environment template
├── .gitignore                       # Git ignore
├── .flake8                          # Linting config
├── pyproject.toml                   # Project config
├── pytest.ini                       # Pytest config
├── requirements.txt                 # Dependencies
├── requirements-lock.txt            # Locked dependencies
└── README.md                        # Project README
```

---

## 🔄 Migration Steps

### Phase 1: Create New Structure (No Breaking Changes)
1. Create new folder structure
2. Copy files to new locations
3. Update imports in copied files
4. Test that everything works

### Phase 2: Update Entry Points
1. Update `run_pipeline.py` → `pipelines/run_data_pipeline.py`
2. Update `model_development_pipeline.py` → `pipelines/run_model_pipeline.py`
3. Create `pipelines/run_full_pipeline.py` for end-to-end

### Phase 3: Clean Up Documentation
1. Move all markdown files to `docs/`
2. Organize by category (guides, reports, specs)
3. Create master `docs/README.md` with links

### Phase 4: Clean Up Scripts
1. Move demo scripts to `scripts/demos/`
2. Move analysis scripts to `scripts/analysis/`
3. Move test scripts to `tests/`

### Phase 5: Remove Old Structure
1. Delete old folders (after verifying new structure works)
2. Update all documentation
3. Update README with new structure

---

## 📋 Detailed Migration Plan

### Step 1: Create `src/` Directory
```bash
mkdir src
mkdir src/ingestion src/processing src/features src/models src/evaluation src/utils
```

**Move files:**
- `modules/ingestion/*` → `src/ingestion/`
- `modules/processing/*` → `src/processing/`
- `feature_engineering/*` → `src/features/`
- `models/*` → `src/models/`
- `evaluation/*` → `src/evaluation/`
- `utils/*` → `src/utils/`

### Step 2: Create `pipelines/` Directory
```bash
mkdir pipelines
```

**Move/Rename files:**
- `run_pipeline.py` → `pipelines/run_data_pipeline.py`
- `model_development_pipeline.py` → `pipelines/run_model_pipeline.py`
- Create `pipelines/run_full_pipeline.py` (new)

### Step 3: Create `scripts/` Directory
```bash
mkdir scripts scripts/demos scripts/analysis scripts/verification
```

**Move files:**
- `demo_*.py` → `scripts/demos/`
- `eda_*.py`, `run_eda.py`, `generate_visualizations.py` → `scripts/analysis/`
- `check_*.py`, `test_gee_access.py`, `verify_*.py`, `fetch_*.py` → `scripts/verification/`

### Step 4: Organize `docs/` Directory
```bash
mkdir docs/guides docs/reports docs/specs docs/api
```

**Move files:**
- `QUICK_START_*.md`, `*_GUIDE.md` → `docs/guides/`
- `*_STATUS.md`, `*_REPORT.md`, `*_SUMMARY.md` → `docs/reports/`
- `.kiro/specs/*` → `docs/specs/`
- `*_API.md` → `docs/api/`

### Step 5: Organize `outputs/` Directory
```bash
mkdir outputs/data outputs/data/raw outputs/data/processed
mkdir outputs/models/production
mkdir outputs/evaluation/latest
mkdir outputs/visualizations/eda outputs/visualizations/models
```

**Reorganize:**
- `outputs/processed/*` → `outputs/data/processed/`
- Create date-based subdirectories for models and evaluations

### Step 6: Create `configs/` Directory
```bash
mkdir configs
```

**Create config files:**
- Extract hardcoded configs to YAML files
- `model_config.yaml`, `data_config.yaml`, `pipeline_config.yaml`

---

## 🎯 Benefits of New Structure

### 1. **Clear Separation of Concerns**
- `src/` - All source code
- `pipelines/` - Entry points
- `scripts/` - Utilities and demos
- `tests/` - All tests
- `docs/` - All documentation
- `outputs/` - All outputs

### 2. **Easier Navigation**
- Know exactly where to find things
- Logical grouping by function
- Clear naming conventions

### 3. **Better for Development**
- Easier to import modules
- Clear dependencies
- Better IDE support

### 4. **Better for Production**
- Clear entry points (`pipelines/`)
- Organized outputs by date
- Production models separate from experiments

### 5. **Better Documentation**
- All docs in one place
- Organized by purpose
- Easy to maintain

---

## 🚀 Quick Start After Reorganization

### Run Data Pipeline
```bash
python pipelines/run_data_pipeline.py
```

### Run Model Pipeline
```bash
python pipelines/run_model_pipeline.py
```

### Run Full Pipeline
```bash
python pipelines/run_full_pipeline.py
```

### Run Demos
```bash
python scripts/demos/demo_chirps_processing.py
```

### Run Analysis
```bash
python scripts/analysis/eda_analysis.py
```

---

## 📝 Implementation Checklist

### Phase 1: Structure Creation
- [ ] Create `src/` directory structure
- [ ] Create `pipelines/` directory
- [ ] Create `scripts/` directory structure
- [ ] Create organized `docs/` structure
- [ ] Create `configs/` directory

### Phase 2: File Migration
- [ ] Move source code to `src/`
- [ ] Move pipelines to `pipelines/`
- [ ] Move scripts to `scripts/`
- [ ] Move docs to `docs/`
- [ ] Update all imports

### Phase 3: Testing
- [ ] Test data pipeline
- [ ] Test model pipeline
- [ ] Test all scripts
- [ ] Verify all imports work

### Phase 4: Documentation
- [ ] Update README.md
- [ ] Create docs/README.md
- [ ] Update all guides
- [ ] Create ARCHITECTURE.md

### Phase 5: Cleanup
- [ ] Remove old directories
- [ ] Remove duplicate files
- [ ] Update .gitignore
- [ ] Final testing

---

## ⚠️ Important Notes

1. **Don't delete old structure until new one is tested**
2. **Update imports gradually**
3. **Test after each major change**
4. **Keep backups**
5. **Update documentation as you go**

---

## 🎯 Priority Actions

### High Priority (Do First)
1. ✅ Move markdown docs to `docs/` (reduces root clutter immediately)
2. ✅ Move demo/test scripts to `scripts/` (cleans up root)
3. ✅ Create `pipelines/` with clear entry points

### Medium Priority (Do Next)
4. ⏳ Consolidate `src/` directory
5. ⏳ Organize `outputs/` by date
6. ⏳ Create config files

### Low Priority (Nice to Have)
7. ⏳ Create comprehensive docs/README.md
8. ⏳ Add ARCHITECTURE.md
9. ⏳ Add CHANGELOG.md

---

**Would you like me to start implementing this reorganization?** I can do it incrementally to avoid breaking anything! 🚀
