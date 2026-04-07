# Archive Index

> This file documents what has been archived, when, and where the consolidated content now lives.
> Updated: April 7, 2026

---

## Phase A Restructure (April 7, 2026)

### Deleted — Empty or Near-Empty Files
The following files contained no meaningful content and were deleted:

| File | Reason |
|------|--------|
| `archive/FORECAST_VISUALIZATION_FIX_COMPLETE.md` | Empty |
| `archive/DASHBOARD_METRICS_UPDATE.md` | 3 lines, no content |
| `archive/phase3/DASHBOARD_TEST_R2_PRIORITY_UPDATE.md` | Empty |
| `archive/phase3/DATA_LEAKAGE_FIX_SUMMARY.md` | Empty |
| `archive/phase3/DOCKER_OPTIMIZATION_RESULTS.md` | Empty |
| `archive/phase3/FEATURE_SELECTION_FIX.md` | Empty |
| `archive/phase3/PROJECT_CLEANUP_2024.md` | Empty |
| `archive/phase3/REFINED_PROJECT_ANSWERS.md` | Empty |
| `archive/phase3/SYSTEM_ARCHITECTURE.md` | Empty |
| `archive/phase3/TASK_10_VERIFICATION.md` | Empty |
| `REORGANIZATION_COMPLETE.md` (root) | Empty duplicate |
| `reports/README.md` | 2 lines, no content |

---

### Moved to `archive/legacy-reports/`
Historical status/completion reports from active development (2024–early 2026).
These document *work done*, not *current state*. Current state is in `references/`.

| File | Original Location |
|------|------------------|
| `BEFORE_AFTER_STRUCTURE.md` | `reports/` |
| `CLEANUP_COMPLETE.md` | `reports/` |
| `COMPLETION_SUMMARY.md` | `reports/` |
| `COMPREHENSIVE_PIPELINE_RESULTS.md` | `reports/` |
| `CONFIG_FILES_MIGRATION.md` | `reports/` |
| `EVALUATION_RESULTS_SUMMARY.md` | `reports/` |
| `FINAL_CLEANUP_STATUS.md` | `reports/` |
| `FINAL_MODEL_PIPELINE_REPORT.md` | `reports/` |
| `FINAL_PIPELINE_REPORT.md` | `reports/` |
| `FINAL_REORGANIZATION_STATUS.md` | `reports/` |
| `FOLDER_REORGANIZATION_PLAN.md` | `reports/` |
| `LSTM_ENSEMBLE_FIXED_SUMMARY.md` | `reports/` |
| `MODELS_STATUS_FINAL.md` | `reports/` |
| `MODEL_DEVELOPMENT_STATUS.md` | `reports/` |
| `MULTI_MODEL_PIPELINE_REPORT.md` | `reports/` |
| `PIPELINE_COMPLETE_SUMMARY.md` | `reports/` |
| `PIPELINE_STATUS_REPORT.md` | `reports/` |
| `PIPELINE_SUCCESS_SUMMARY.md` | `reports/` |
| `REORGANIZATION_COMPLETE.md` | `reports/` |
| `REORGANIZATION_SUMMARY.md` | `reports/` |
| `DATA_PIPELINE_TEST_FIXES.md` | `reports/` |
| `CI_CD_FIX.md` | `reports/` |
| `CODEBASE_REVIEW_WALKTHROUGH.md` | `reports/` |
| `ACTUARIAL_FEEDBACK_RESOLUTION.md` | `reports/` |

**Consolidated content now lives in:** `references/DATA_PIPELINE_REFERENCE.md`, `references/ML_MODEL_REFERENCE.md`, `references/TESTING_REFERENCE.md`

---

### Moved to `validation/`
Active backtesting and validation artifacts — moved from `reports/` and `Basis Risk_Validation_Backward Testing/`:

| File | Original Location |
|------|------------------|
| `KILOMBERO_BACKTESTING_REPORT.md` | `reports/` |
| `KILOMBERO_BACKTESTING_REPORT_IN_SAMPLE.md` | `reports/` |
| `KILOMBERO_BACKTESTING_REPORT_OUT_OF_SAMPLE.md` | `reports/` |
| `BACKTESTING_SUMMARY.md` | `Basis Risk_Validation_Backward Testing/` |
| `BACKTESTING_SUMMARY_v2.md` | `Basis Risk_Validation_Backward Testing/` |
| `PHASE_BASED_COMPARISON.md` | `Basis Risk_Validation_Backward Testing/` |
| `BACKTESTING_SUMMARY_v2.pdf` | `Basis Risk_Validation_Backward Testing/` |
| `HewaSense_Retrospective_Validation.pdf` | `Basis Risk_Validation_Backward Testing/` |
| `Comprehensive Analysis of Agronomic Productivity....pdf` | `Basis Risk_Validation_Backward Testing/` |

---

### Renamed Folders
| Old Name | New Name | Reason |
|----------|----------|--------|
| `Kilombero Pilot/` | `pilots/kilombero/` | Extensible structure for future pilots |
| `Basis Risk_Validation_Backward Testing/` | `validation/` | Cleaner name; folder now contains all validation artifacts |

---

## Phase B Restructure (Planned — Post June 2026 Gate)

See Q2 2026 Roadmap in `memory/MEMORY.md` for details. Planned actions:
- Merge 3 pipeline status docs into single `current/PIPELINE_CURRENT_STATUS.md`
- Merge `CLAIMS_MANAGEMENT_DASHBOARD_SPEC.md` into `FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md`
- Create `domains/` folder for parametric insurance + climate science materials
- Create `devops/` folder for GOTCHA framework + deployment + monitoring
- Reorganise `archive/phase3/` (79 files) by topic into subfolders
- Extract HewaSense PDF guides to markdown references
- Merge `BACKTESTING_SUMMARY.md` + `BACKTESTING_SUMMARY_v2.md` into single file
