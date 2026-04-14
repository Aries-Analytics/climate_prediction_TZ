# Tanzania Climate Intelligence Platform - Documentation

**Last Updated**: April 14, 2026
**Status**: 🔵 Shadow Run v2 ACTIVE (Apr 14 – Jul 13, 2026 · Ifakara TC + Mlimba DC)
**Version**: 3.5 (Phase A restructure — pilots/, validation/, legacy-reports/ archived)

---

## 🚀 Quick Start

**New to the project?** Start here:

1. **[GETTING_STARTED.md](./guides/GETTING_STARTED.md)** - 5-minute setup guide
2. **[PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md)** - Complete system overview
3. **[EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md)** - Key achievements and metrics

---

## 📚 Core Documentation (Single Sources of Truth)

### Essential References (All in [references/](./references/))

| Document | Description | Key Content |
|----------|-------------|-------------|
| **[PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md)** ⭐ | Complete project overview | System capabilities, performance metrics, technical journey |
| **[DATA_PIPELINE_REFERENCE.md](./references/DATA_PIPELINE_REFERENCE.md)** | Data pipeline architecture | 5 data sources, 6 locations, ingestion & processing |
| **[ML_MODEL_REFERENCE.md](./references/ML_MODEL_REFERENCE.md)** | ML models and training | XGBoost (R²=0.8666), Random Forest, LSTM, Ensemble |
| **[TESTING_REFERENCE.md](./references/TESTING_REFERENCE.md)** | Testing strategy | 180+ tests, 80%+ coverage, validation framework |
| **[FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md](./references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md)** | Dashboard system | 5 interactive dashboards, visualizations |
| **[PARAMETRIC_INSURANCE_FINAL.md](./references/PARAMETRIC_INSURANCE_FINAL.md)** | Insurance implementation | Payout model, triggers, financial sustainability |
| **[data_dictionary.md](./references/data_dictionary.md)** | Data schemas | Complete data schemas and definitions |

### User Guides (All in [guides/](./guides/))

| Document | Description |
|----------|-------------|
| **[GETTING_STARTED.md](./guides/GETTING_STARTED.md)** | Quick start guide and setup instructions |
| **[SETUP_GUIDES.md](./guides/SETUP_GUIDES.md)** | Detailed setup procedures |
| **[CLI_USAGE_GUIDE.md](./guides/CLI_USAGE_GUIDE.md)** | Command-line interface documentation |
| **[BUSINESS_REPORTS_GUIDE.md](./guides/BUSINESS_REPORTS_GUIDE.md)** | Business reporting features |
| **[MODEL_PIPELINE_README.md](./guides/MODEL_PIPELINE_README.md)** | ML pipeline usage guide |
| **[QUICK_START_PROCESSING.md](./guides/QUICK_START_PROCESSING.md)** | Data processing quick start |
| **[AUTOMATED_PIPELINE_DEPLOYMENT.md](./guides/AUTOMATED_PIPELINE_DEPLOYMENT.md)** | Production deployment guide |
| **[DEV_DEPLOYMENT.md](./guides/DEV_DEPLOYMENT.md)** | Dev environment deployment |
| **[MONITORING_GUIDE.md](./guides/MONITORING_GUIDE.md)** | Monitoring & observability |
| **[TESTING_MONITORING_REFERENCE.md](./guides/TESTING_MONITORING_REFERENCE.md)** | Testing & monitoring quick reference |

### Current Status & Verification (All in [current/](./current/))

| Document | Description |
|----------|-------------|
| **[6_LOCATION_EXPANSION_SUMMARY.md](./current/6_LOCATION_EXPANSION_SUMMARY.md)** | 6-location expansion details (source of truth) |
| **[EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md)** | Executive summary with latest metrics |
| **[CRITICAL_NUMBERS_VERIFICATION.md](./current/CRITICAL_NUMBERS_VERIFICATION.md)** | Verified system metrics |
| **[CONSOLIDATION_SUMMARY.md](./current/CONSOLIDATION_SUMMARY.md)** | Documentation consolidation record |
| **[CONSOLIDATION_INVENTORY.md](./current/CONSOLIDATION_INVENTORY.md)** | Complete inventory of all documents |

---

## 📊 System Overview

### Key Metrics (6-Location System)

| Metric | Value |
|--------|-------|
| **Production Pilot** | 1 (Morogoro — Kilombero Basin, 1,000 rice farmers) |
| **Training Locations** | 6 (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza, Morogoro) |
| **Data Sources** | 5 (NASA POWER, ERA5, CHIRPS, NDVI, Ocean Indices) |
| **Total Samples** | 1,872 (6 locations × 312 months) |
| **Time Period** | 26 years (2000-2025) |
| **Features** | 83 (selected from 245 post-leakage-removal) |
| **Model Accuracy** | 0.8666 R² (XGBoost, data leakage fix) |
| **Spatial CV R²** | 0.8566 ± 0.0575 (RF, 5-fold temporal CV) |
| **Dashboards** | 5 interactive dashboards |
| **API Endpoints** | 28 endpoints |
| **Test Coverage** | 80%+ (180+ tests) |

### Technology Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Python 3.11
- **Frontend**: React 18, TypeScript, Material-UI, Plotly.js
- **ML**: XGBoost, Random Forest, LSTM, scikit-learn
- **Infrastructure**: Docker, Nginx, GitHub Actions

### Key Features

- ✅ **86.7% prediction accuracy** (XGBoost R²=0.8666, 6-location training, data leakage fix)
- ✅ **Morogoro production pilot** — Kilombero Basin, 1,000 rice farmers
- ✅ **5 authoritative data sources** integrated
- ✅ **5 interactive dashboards**
- ✅ **Automated pipeline** with scheduling
- ✅ **Production-ready deployment**
- ✅ **Comprehensive testing** (80%+ coverage)

---

## 🎯 Documentation by Role

### For Developers

**Getting Started**:
- [GETTING_STARTED.md](./guides/GETTING_STARTED.md) - Setup and quick start
- [SETUP_GUIDES.md](./guides/SETUP_GUIDES.md) - Detailed setup procedures
- [CLI_USAGE_GUIDE.md](./guides/CLI_USAGE_GUIDE.md) - CLI commands

**Development**:
- [DATA_PIPELINE_REFERENCE.md](./references/DATA_PIPELINE_REFERENCE.md) - Data pipeline
- [ML_MODEL_REFERENCE.md](./references/ML_MODEL_REFERENCE.md) - ML models
- [TESTING_REFERENCE.md](./references/TESTING_REFERENCE.md) - Testing strategy
- [data_dictionary.md](./references/data_dictionary.md) - Data schemas

**Advanced**:
- [guides/](./guides/) - Detailed how-to guides
- [api/](./api/) - API documentation
- [specs/](./specs/) - Technical specifications

### For Data Scientists

**ML & Models**:
- [ML_MODEL_REFERENCE.md](./references/ML_MODEL_REFERENCE.md) - Model development
- [DATA_PIPELINE_REFERENCE.md](./references/DATA_PIPELINE_REFERENCE.md) - Data processing
- [6_LOCATION_EXPANSION_SUMMARY.md](./current/6_LOCATION_EXPANSION_SUMMARY.md) - Latest results
- [data_dictionary.md](./references/data_dictionary.md) - Data schemas

**Performance**:
- [CRITICAL_NUMBERS_VERIFICATION.md](./current/CRITICAL_NUMBERS_VERIFICATION.md) - Verified metrics
- [EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md) - Performance summary

### For Stakeholders

**Executive View**:
- [EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md) - Key achievements
- [PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md) - Complete overview
- [6_LOCATION_EXPANSION_SUMMARY.md](./current/6_LOCATION_EXPANSION_SUMMARY.md) - Latest expansion

**Business Case**:
- [PARAMETRIC_INSURANCE_FINAL.md](./references/PARAMETRIC_INSURANCE_FINAL.md) - Insurance model
- [BUSINESS_REPORTS_GUIDE.md](./guides/BUSINESS_REPORTS_GUIDE.md) - Business reporting
- [FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md](./references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md) - Dashboard features

### For Operations

**Deployment**:
- [GETTING_STARTED.md](./guides/GETTING_STARTED.md) - Quick deployment
- [SETUP_GUIDES.md](./guides/SETUP_GUIDES.md) - Detailed setup

**Maintenance**:
- [CLI_USAGE_GUIDE.md](./guides/CLI_USAGE_GUIDE.md) - CLI operations
- [TESTING_REFERENCE.md](./references/TESTING_REFERENCE.md) - Testing procedures

---

## 📁 Additional Resources

### Specialized Documentation

- **[guides/](./guides/)** - User guides and how-to documentation
  - [GETTING_STARTED.md](./guides/GETTING_STARTED.md) - Quick start guide
  - [SETUP_GUIDES.md](./guides/SETUP_GUIDES.md) - Detailed setup
  - [CLI_USAGE_GUIDE.md](./guides/CLI_USAGE_GUIDE.md) - CLI documentation
  - [BUSINESS_REPORTS_GUIDE.md](./guides/BUSINESS_REPORTS_GUIDE.md) - Business reporting
  - [MODEL_PIPELINE_README.md](./guides/MODEL_PIPELINE_README.md) - ML pipeline usage
  - [QUICK_START_PROCESSING.md](./guides/QUICK_START_PROCESSING.md) - Data processing
  - [AUTOMATED_PIPELINE_DEPLOYMENT.md](./guides/AUTOMATED_PIPELINE_DEPLOYMENT.md) - Production deployment
  - [MOROGORO_PILOT_CONFIGURATION.md](./pilots/kilombero/MOROGORO_PILOT_CONFIGURATION.md) - Pilot setup

- **[references/](./references/)** - Core reference documents (sources of truth)
  - [PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md) - Complete overview
  - [DATA_PIPELINE_REFERENCE.md](./references/DATA_PIPELINE_REFERENCE.md) - Pipeline architecture
  - [ML_MODEL_REFERENCE.md](./references/ML_MODEL_REFERENCE.md) - ML models
  - [TESTING_REFERENCE.md](./references/TESTING_REFERENCE.md) - Testing strategy
  - [FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md](./references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md) - Dashboards
  - [PARAMETRIC_INSURANCE_FINAL.md](./references/PARAMETRIC_INSURANCE_FINAL.md) - Insurance
  - [data_dictionary.md](./references/data_dictionary.md) - Data schemas

- **[current/](./current/)** - Current status and verification documents
  - [6_LOCATION_EXPANSION_SUMMARY.md](./current/6_LOCATION_EXPANSION_SUMMARY.md) - Latest expansion
  - [JANUARY_2026_PIPELINE_IMPROVEMENTS.md](./current/JANUARY_2026_PIPELINE_IMPROVEMENTS.md) - Recent pipeline fixes
  - [EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md) - Executive summary
  - [CRITICAL_NUMBERS_VERIFICATION.md](./current/CRITICAL_NUMBERS_VERIFICATION.md) - Verified metrics
  - [CONSOLIDATION_SUMMARY.md](./current/CONSOLIDATION_SUMMARY.md) - Consolidation record

- **[diagrams/](./diagrams/)** - System architecture diagrams
  - [architecture.md](./diagrams/architecture.md) - System architecture
  - [dataflow.md](./diagrams/dataflow.md) - Data flow diagrams
  - [sequence.md](./diagrams/sequence.md) - Sequence diagrams

- **[pilots/kilombero/](./pilots/kilombero/)** - Kilombero Basin pilot operations
  - [KILOMBERO_BASIN_PILOT_SPECIFICATION.md](./pilots/kilombero/KILOMBERO_BASIN_PILOT_SPECIFICATION.md) - Active pilot spec
  - [SHADOW_RUN_DEPLOYMENT_GUIDE.md](./pilots/kilombero/SHADOW_RUN_DEPLOYMENT_GUIDE.md) - Deployment guide
  - [MOROGORO_PILOT_CONFIGURATION.md](./pilots/kilombero/MOROGORO_PILOT_CONFIGURATION.md) - Pilot configuration
  - [MODEL_METRICS_AND_SHADOW_RUN_IMPLICATIONS.md](./pilots/kilombero/MODEL_METRICS_AND_SHADOW_RUN_IMPLICATIONS.md) - Metrics
  - [MEDIUM_ARTICLE_PART_2_FINAL.md](./pilots/kilombero/MEDIUM_ARTICLE_PART_2_FINAL.md) - Public write-up

- **[validation/](./validation/)** - Backtesting and basis risk validation
  - [PHASE_BASED_COMPARISON.md](./validation/PHASE_BASED_COMPARISON.md) - Phase-based model comparison (master)
  - [KILOMBERO_BACKTESTING_REPORT.md](./validation/KILOMBERO_BACKTESTING_REPORT.md) - Full backtesting report
  - [KILOMBERO_BACKTESTING_REPORT_IN_SAMPLE.md](./validation/KILOMBERO_BACKTESTING_REPORT_IN_SAMPLE.md) - In-sample
  - [KILOMBERO_BACKTESTING_REPORT_OUT_OF_SAMPLE.md](./validation/KILOMBERO_BACKTESTING_REPORT_OUT_OF_SAMPLE.md) - Out-of-sample
  - [BACKTESTING_SUMMARY_v2.md](./validation/BACKTESTING_SUMMARY_v2.md) - Summary (current)
  - Supporting PDFs: HewaSense_Retrospective_Validation.pdf, BACKTESTING_SUMMARY_v2.pdf

- **[archive/](./archive/)** - Historical documentation (superseded)
  - [archive/_INDEX.md](./archive/_INDEX.md) - What was consolidated where and when
  - [archive/phase1/](./archive/phase1/) - Phase 1 (single location, 2010-2025)
  - [archive/phase2/](./archive/phase2/) - Phase 2 (5 locations)
  - [archive/phase3/](./archive/phase3/) - Phase 3 superseded documents
  - [archive/legacy-reports/](./archive/legacy-reports/) - Historical status/completion reports

### Quick Reference

**For Stakeholders**:
- [EXECUTIVE_SUMMARY.md](./current/EXECUTIVE_SUMMARY.md) - Complete overview
- [PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md) - Validated summary
- [PARAMETRIC_INSURANCE_FINAL.md](./references/PARAMETRIC_INSURANCE_FINAL.md) - Insurance implementation

**For Data**:
- [data_dictionary.md](./references/data_dictionary.md) - Data schemas
- [DATA_PIPELINE_REFERENCE.md](./references/DATA_PIPELINE_REFERENCE.md) - Pipeline architecture

**For Models**:
- [ML_MODEL_REFERENCE.md](./references/ML_MODEL_REFERENCE.md) - Model development
- [6_LOCATION_EXPANSION_SUMMARY.md](./current/6_LOCATION_EXPANSION_SUMMARY.md) - Latest results

**For Business**:
- [BUSINESS_REPORTS_GUIDE.md](./guides/BUSINESS_REPORTS_GUIDE.md) - Business reporting
- [PARAMETRIC_INSURANCE_FINAL.md](./references/PARAMETRIC_INSURANCE_FINAL.md) - Insurance calibration

**For CLI**:
- [CLI_USAGE_GUIDE.md](./guides/CLI_USAGE_GUIDE.md) - Command-line interface

**For Dashboards**:
- [FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md](./references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md) - Complete overview

---

## 📞 Support

### Need Help?

1. **Getting Started**: See [GETTING_STARTED.md](./guides/GETTING_STARTED.md)
2. **Technical Questions**: See [PROJECT_OVERVIEW_CONSOLIDATED.md](./references/PROJECT_OVERVIEW_CONSOLIDATED.md)
3. **Data Questions**: See [data_dictionary.md](./references/data_dictionary.md)
4. **Dashboard Usage**: See [FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md](./references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md)

### Documentation Issues

If you find:
- Broken links
- Outdated information
- Missing documentation
- Unclear explanation

Please create an issue or update the relevant core document.

---

## 📝 Documentation Standards

### When to Update

**Feature changes**: Update relevant core documents
- New features → Add to appropriate reference
- Bug fixes → Update if documentation affected
- Performance metrics → Update CRITICAL_NUMBERS_VERIFICATION.md

**How to Update**

1. **Find the right document** - Use this README to locate
2. **Update the content** - Make changes
3. **Update "Last Updated"** - Keep current date
4. **Check cross-references** - Ensure links work
5. **Verify code examples** - Test still works

---

## 🆕 What's New

### April 2026 - Documentation Restructure & Pipeline Stability

- ✅ **Docs Phase A restructure** — `pilots/kilombero/`, `validation/`, `archive/legacy-reports/` created; stale root files cleared
- ✅ **Pipeline stability** — tz-naive/tz-aware TypeError fixed (chirps, nasa_power, ndvi); ERA5 date/datetime TypeError fixed
- ✅ **All 4 data sources clean** — chirps, nasa_power, ndvi confirmed Apr 7; era5 fix deployed, expected clean Apr 8
- ✅ **Scripts reorganised** — `train_pipeline.py`, `run_evaluation.py`, `audit.py`, `verify_data_leakage.py` moved to `scripts/`

### March 2026 - Shadow Run Launch & Platform Hardening

- ✅ **Shadow run active** — daily pipeline at 6 AM EAT, Apr 14 – Jul 13, 2026 (90 run-days, 2,160 forecast target — two-zone Kilombero split: Ifakara TC + Mlimba DC)
- ✅ **Public landing page live** — `hewasense.majaribio.com`
- ✅ **Evidence Pack dashboard** — live run-day counter, forecast accumulation, execution history
- ✅ **Phase-Based Dynamic Model deployed** — 4-phase GDD tracker, 20% basis risk, 100% catch rate on confirmed disasters
- ✅ **Probabilistic trigger system** — `norm.cdf()` replacing sigmoid; physical Kilombero thresholds from `configs/trigger_thresholds.yaml`
- ✅ **Stage 6 auto-log** — daily pipeline commits session notes and updates 5 business docs autonomously
- ✅ **Shadow run completion automation** — Stage 5 detects day-90, generates final Evidence Pack + Brier Score report automatically

### January–February 2026 - Foundation

- ✅ **Data pipeline** — 5 sources, incremental ingestion, month-capping, partial-month guards
- ✅ **Model training** — XGBoost R²=0.8666 (83 features, 11 leaky features removed)
- ✅ **Testing infrastructure** — 180+ tests, 80%+ coverage, mock APIs
- ✅ **Docker deployment** — `docker-compose.dev.yml`, systemd auto-restart on server reboot
- ✅ **Scheduler** — `CronTrigger` with explicit EAT timezone, in-memory job store, advisory lock (NullPool)

---

## 🎯 Project Status

**Phase**: Forward Validation (Shadow Run)
**Version**: 3.5
**Last Updated**: April 14, 2026
**Status**: 🔵 Shadow Run v2 ACTIVE (Apr 14 – Jul 13, 2026 · Ifakara TC + Mlimba DC)

**Current state**:
- ✅ All features implemented and documented
- ✅ Comprehensive testing (180+ tests, 80%+ coverage)
- ✅ Docker-ready deployment (live at hewasense.majaribio.com)
- ✅ Documentation restructured (Phase A complete)
- ✅ Yield ground truth calibrated — two-zone: Ifakara TC 2.30 MT/Ha, Mlimba DC 2.59 MT/Ha
- ✅ Zone-split evaluation layer — per-zone Brier/RMSE/ECE, basis risk, GO/NO-GO gates
- 🔵 Forward validation in progress — first per-zone Brier Scores ~Jul 10, 2026
- ⏳ Go/No-Go decision mid-2026 → underwriter engagement Q3 → pilot alignment Q4

---

**Main README**: [../README.md](../README.md) - Project root documentation  
**Backend Docs**: `backend/` - Backend-specific documentation  
**Frontend Docs**: `frontend/` - Frontend-specific documentation
