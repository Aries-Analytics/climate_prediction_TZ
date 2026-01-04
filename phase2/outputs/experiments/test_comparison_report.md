# Experiment Comparison Report
Generated: 2025-11-15 07:40:48
Total Experiments: 3

---

## Summary Statistics

| Metric | Mean | Std | Min | Max |
|--------|------|-----|-----|-----|
| r2 | 0.8767 | 0.0306 | 0.8500 | 0.9100 |
| rmse | 12.1667 | 1.8230 | 10.2000 | 13.8000 |
| mae | 9.2667 | 1.5695 | 7.5000 | 10.5000 |

---

## Top 5 Experiments

| Rank | Experiment ID | Timestamp |
|------|---------------|------------|
| 2 | test_xgb_20251115_074048 | 2025-11-15T07:40:48.392415 |
| 1 | test_rf_20251115_074048 | 2025-11-15T07:40:48.388611 |
| 3 | test_lstm_20251115_074048 | 2025-11-15T07:40:48.395582 |

---

## All Experiments

Total: 3 experiments

| experiment_id | timestamp | model_type | hyperparameters | r2 | rmse | mae | training_time |
|---|---|---|---|---|---|---|---|
| test_rf_20251115_074048 | 2025-11-15T07:40:48.388611 | random_forest | {'n_estimators': 200, 'max_depth': 15} | 0.8700 | 12.5000 | 9.8000 | 45.2000 |
| test_xgb_20251115_074048 | 2025-11-15T07:40:48.392415 | xgboost | {'n_estimators': 200, 'max_depth': 8, 'learning_ra... | 0.9100 | 10.2000 | 7.5000 | 62.8000 |
| test_lstm_20251115_074048 | 2025-11-15T07:40:48.395582 | lstm | {'units': [128, 64], 'dropout': 0.2, 'epochs': 100... | 0.8500 | 13.8000 | 10.5000 | 180.5000 |
