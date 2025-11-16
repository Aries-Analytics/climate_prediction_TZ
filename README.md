# Tanzania Climate Prediction

A comprehensive end-to-end machine learning system for climate prediction in Tanzania.

## 📂 Project Structure

This repository contains the Tanzania Climate Prediction project:

- **[Phase 2](phase2/)** - Complete ML system with data pipeline, feature engineering, and model training ✅ **ACTIVE**

## 🚀 Quick Start

```bash
# Navigate to phase2
cd phase2

# Run data pipeline
python run_pipeline.py

# Train models
python model_development_pipeline.py
```

## 📖 Full Documentation

**See [Phase 2 README](phase2/README.md) for complete documentation**

### Key Features

✅ **Data Pipeline** - 5 sources integrated (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices)  
✅ **ML Models** - Random Forest, XGBoost, LSTM, Ensemble  
✅ **Performance** - R² > 0.85 target with uncertainty quantification  
✅ **Production Ready** - 45+ tests, experiment tracking, clean architecture  

### Documentation Links

- **[Phase 2 README](phase2/README.md)** - Complete documentation
- **[Model Development Guide](phase2/docs/MODEL_DEVELOPMENT_GUIDE.md)** - ML pipeline usage
- **[Pipeline Overview](phase2/docs/pipeline_overview.md)** - Architecture details
- **[Implementation Status](phase2/docs/IMPLEMENTATION_STATUS.md)** - Project progress

### Architecture

```
phase2/
 modules/           # Data ingestion & domain processing
 preprocessing/     # ML feature engineering
 pipelines/         # Pipeline orchestration (3 pipelines)
 models/            # Model implementations (4 models)
 evaluation/        # Evaluation utilities
 tests/             # 45+ comprehensive tests
 docs/              # Documentation
```

### Models

| Model | Description |
|-------|-------------|
| Random Forest | 200 trees, feature importance |
| XGBoost | Gradient boosting, early stopping |
| LSTM | 2-layer neural network, time series |
| Ensemble | Weighted average of all models |

---

**For complete documentation, installation, usage, and troubleshooting, see [Phase 2 README](phase2/README.md)**
