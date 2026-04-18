# HewaSense

Climate intelligence for parametric crop insurance in Tanzania.

HewaSense is an end-to-end ML system that generates probabilistic climate forecasts to power index-based insurance for smallholder farmers. It ingests data from 5 climate sources, runs daily forecasts through a phase-aware trigger model, and serves results via a React dashboard and REST API.

**Live dashboard**: [hewasense.majaribio.com](https://hewasense.majaribio.com)

## Current Status

**Shadow Run v2** (Apr 16 -- Jul 14, 2026) -- 90-day forward validation generating 24 forecasts/day across two Kilombero Basin zones (Ifakara TC + Mlimba DC). Accumulating Brier Scores for reinsurer evidence pack.

- **Pilot**: 1,000 rice farmers, Kilombero Basin, Morogoro, Tanzania
- **Production model**: XGBoost, R² = 0.8666 (83 features, post-leakage fix)
- **Basis risk**: 20% (Phase-Based Dynamic Model)
- **Premium**: $20/farmer/year, Loss ratio: 22.6% (retrospective)
- **Payout SLA**: 5--7 business days from trigger confirmation

## Architecture

```
phase2/
  backend/          FastAPI app + pipeline scheduler + services
  frontend/         React 18 + TypeScript + Material-UI (7 dashboard views)
  configs/          Trigger thresholds, pipeline config
  models/           ML model implementations (XGBoost, RF, LSTM, Ensemble)
  data/             Climate data + ground truth
  docs/             Full documentation
  tests/            180+ tests
  scripts/          Deployment, training, evaluation
```

**Data sources**: NASA POWER, ERA5, CHIRPS, NDVI, NOAA Ocean Indices

**Pipeline**: Runs daily at 6 AM EAT via Docker on a Hetzner server. Ingests latest climate data, generates forecasts for 3 trigger types (drought, flood, crop failure) across 4 horizons and 2 zones, logs results to PostgreSQL, and sends Slack alerts.

## Quick Start

```bash
# Clone and start the full stack
git clone https://github.com/Aries-Analytics/climate_prediction_TZ.git
cd climate_prediction_TZ/phase2

# Configure environment
cp .env.template .env
# Edit .env with your API keys (ERA5, NASA POWER, Slack webhook)

# Start all services (backend, frontend, scheduler, DB)
docker compose -f docker-compose.dev.yml up -d

# Dashboard at http://localhost:3000
# API docs at http://localhost:8000/docs
```

## ML Training

```bash
cd phase2

# Full training pipeline (feature selection + training + evaluation)
python scripts/train_pipeline.py

# Quick prototype
python pipelines/quick_model_pipeline.py

# Run tests
pytest -v
```

## Deployment

```bash
# Deploy to server (auto-detects init vs update)
./phase2/scripts/deploy.sh shadow-run
```

See [phase2/docs/guides/AUTOMATED_PIPELINE_DEPLOYMENT.md](phase2/docs/guides/AUTOMATED_PIPELINE_DEPLOYMENT.md) for full deployment docs.

## Documentation

| Document | Description |
|----------|-------------|
| [Executive Summary](phase2/docs/current/EXECUTIVE_SUMMARY.md) | Latest status, metrics, next steps |
| [ML Model Reference](phase2/docs/references/ML_MODEL_REFERENCE.md) | Inference chain, training, CDF conversion |
| [Parametric Insurance](phase2/docs/references/PARAMETRIC_INSURANCE_FINAL.md) | Trigger model, financials, actuarial analysis |
| [Kilombero Pilot Spec](phase2/docs/pilots/kilombero/KILOMBERO_BASIN_PILOT_SPECIFICATION.md) | Pilot design and operations |
| [Getting Started](phase2/docs/guides/GETTING_STARTED.md) | 5-minute local setup with Docker |
| [Monitoring Guide](phase2/docs/guides/MONITORING_GUIDE.md) | Health checks and alerting |
| [Full docs index](phase2/docs/README.md) | Complete documentation directory |

## Key Technical Details

- **Probabilistic triggers**: Uses `norm.cdf()` with physical Kilombero thresholds -- more defensible than static percentile triggers used in traditional weather index insurance
- **Phase-Based Dynamic Model**: 4-phase GDD tracker catches 100% of confirmed crop disasters (2017/18 and 2021/22) with zero false negatives
- **Zone-aware evaluation**: All metrics, basis risk, and GO/NO-GO gates are computed per-zone (Ifakara TC + Mlimba DC) and aggregate
- **Spatial validation**: CHIRPS 5km grid correlates at r=0.888 against local gauges

## License

This project is part of the HewaSense climate intelligence initiative by [Aries Analytics](https://github.com/Aries-Analytics).
