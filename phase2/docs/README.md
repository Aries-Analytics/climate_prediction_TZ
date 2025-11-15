# Tanzania Climate Prediction - Documentation

## Documentation Index

### Quick Start Guides
- [Quick Start Processing](guides/QUICK_START_PROCESSING.md) - Get started with data processing
- [Model Pipeline Guide](guides/MODEL_PIPELINE_README.md) - Train and evaluate models
- [Evaluation Reports Guide](guides/VIEW_EVALUATION_REPORTS.md) - View model results

### Status Reports
- [Pipeline Status](reports/PIPELINE_STATUS_REPORT.md) - Data pipeline status
- [Model Status](reports/MODELS_STATUS_FINAL.md) - Model training status
- [Evaluation Results](reports/EVALUATION_RESULTS_SUMMARY.md) - Latest model results
- [Complete Summary](reports/PIPELINE_COMPLETE_SUMMARY.md) - Full pipeline summary

### Technical Documentation
- [Architecture](ARCHITECTURE.md) - System architecture
- [API Documentation](api/) - API references
- [Specifications](specs/) - Technical specifications

### Development
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

---

## Project Structure

```
tanzania-climate-prediction/
├── src/              # Source code
├── pipelines/        # Main pipeline scripts
├── scripts/          # Utility scripts
├── tests/            # Tests
├── docs/             # Documentation (you are here)
├── outputs/          # All outputs
└── configs/          # Configuration files
```

## Common Tasks

### Run Data Pipeline
```bash
python pipelines/run_data_pipeline.py
```

### Run Model Pipeline
```bash
python pipelines/run_model_pipeline.py
```

### View Latest Results
```bash
# Check outputs/evaluation/latest/
```

---

For more information, see the main [README.md](../README.md)
