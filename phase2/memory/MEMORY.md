# Persistent Memory

> This file contains curated long-term facts, preferences, and context that persist across sessions.
> The AI reads this at the start of each session. You can edit this file directly.

## Project Overview

- **Project:** HewaSense — Climate intelligence for parametric crop insurance (Tanzania)
- **Framework:** GOTCHA (6-layer) + ATLAS (build workflow) + 4-Persona model
- **Current Phase:** Shadow-Run Forward Testing (Phase 4.0)
- **Pilot:** Morogoro (Kilombero Basin), 1000 rice farmers
- **Production Model:** Phase-Based Dynamic Model (4-phase GDD tracker)

## Key Facts

- **Production ML Model:** XGBoost, Test R²=0.8666 (86.7%) — primary serving model (post data leakage fix, 11 rainfall-derived features removed)
- **Ensemble R²:** 0.8402 (secondary model, not used for forward predictions)
- **98.4%/98.3%:** Single-location/older dataset benchmarks — historical only, NOT the production number
- **Basis Risk:** 20% (Phase-Based Dynamic Model) — production. 10% (April threshold) — baseline only.
- **Phase-Based Model:** Catches 100% of confirmed crop disasters (2017/2018 and 2021/2022), zero false negatives
- **Premium:** $20/farmer/year, Loss Ratio: 22.6% (retrospective; forward validation ACTIVE — shadow run Mar 7 – Jun 5, 2026)
- **HewaSense Engine V4 (Feb 2026):** Dynamic GDD tracking, cumulative flood limits (120-160mm over 5 days)
- **Out-of-Sample Validation:** 9.6% historic loss ratio (2000-2014)
- **Spatial Validation:** CHIRPS 5km grid correlated at r=0.888 against local gauges
- PILOT_LOCATION_ID = 6 (Morogoro)
- Payout threshold = 75%
- Models expect **83 features** (retrained Mar 2026; 11 leaky rainfall-derived features removed from 279, leaving 245 candidates; 83 selected)
- Feature schema: `feature_selection_results.json` (83 features, single source of truth)
- Law #8 (AUTONOMOUS DOCUMENTATION) mandates doc updates after any model/config change
- **Production model file:** Determined by `outputs/models/active_model.json` (currently `xgboost_climate.pkl`, R²=0.8666, 83 features). NEVER hardcode model names
- Model selection driven entirely by `active_model.json` — if missing or invalid, fail explicitly (GOTCHA Law #1)
- **Pipeline schedule (shadow-run ACTIVE):** `0 6 * * *` Africa/Dar_es_Salaam (6 AM EAT daily). Deployed to `root@37.27.200.227`, `docker-compose.dev.yml`. Scheduler confirmed next run `2026-03-09 06:00:00+03:00`.
- **Pipeline status (March 2026):** Shadow run ACTIVE Mar 7 – Jun 5, 2026. 12 forecasts/run (3 triggers × 4 horizons × Morogoro). Evidence Pack accumulates; Brier Score auto-evaluation starts ~Jun 8.
- Lock contention alerts are suppressed in Slack (expected during brief overlaps)
- **Advisory lock:** Uses a **dedicated raw DB connection** (separate from ORM session). ORM `commit()` works normally without releasing the lock. Lock released by closing the dedicated connection.
- **Scheduler job store:** In-memory (NOT persistent SQLAlchemyJobStore). Prevents phantom runs from stale `next_run_times` after container restarts.
- Scheduler clears stale advisory locks on startup (`_clear_stale_locks()` terminates old PostgreSQL backends)
- Forecast lookback: 7 months + `.replace(day=1)` to capture ≥6 monthly records
- **ERA5 client:** `ecmwf-datastores-client` (v0.4.2) — migrated from deprecated `cdsapi` which had connection/DNS failures. New client uses `ECMWF_DATASTORES_URL`/`ECMWF_DATASTORES_KEY` env vars.
- **No synthetic data fallbacks** (GOTCHA Law #1): if critical data sources fail, forecasts are skipped — never filled with zeros

## Documentation Tone (Expert Feedback — March 2026)

- **Never use "production-ready"** → use "pilot-ready" or "forward validation phase"
- **Always qualify accuracy numbers** with dataset context (single-location vs 6-location)
- **Include Known Limitations** in all externally-facing docs
- **Yield ground truth:** Currently national averages (NBS/USDA-FAS), not Kilombero-specific
- **Data resolution:** CHIRPS (5km) vs NASA POWER (50km) mismatch documented, mitigation planned (rain gauges)
- **Historical reports** in `docs/reports/` and `docs/archive/` are never modified

## GOTCHA Layer Locations

- Goals: `goals/manifest.md` → individual goal files
- Tools: `tools/manifest.md` → scripts index
- Context: `context/` → domain knowledge
- Hard Prompts: `hardprompts/` → templates
- Args: `args/persona_config.yaml`

## Known Bugs Fixed (Mar 2026)

- **ERA5 400 Bad Request:** ECMWF rejects current incomplete month. Fix: cap `range(1, last_complete_month+1)` in `fetch_era5_data()` AND cap `end_date` in `ingest_era5()`. File: `backend/modules/ingestion/era5_ingestion.py`. Fixed 2026-03-07.
- **ForecastLog never auto-evaluated:** Stage 3 added to `orchestrator.py:execute_pipeline()` on 2026-03-07.
- **Scheduler fires at wrong time (UTC not EAT):** `CronTrigger.from_crontab()` must receive `timezone=self.timezone` explicitly — not inherited from `BackgroundScheduler(timezone=...)`. Fixed 2026-03-08 in `backend/app/services/pipeline/scheduler.py:215`.
- **Climate data seed loaded 313 rows instead of 1,878:** `load_climate_data.py` hardcoded `TANZANIA_LAT/LON` for all rows, collapsing 6-location upsert. Fix: per-row `row_lat/row_lon` from CSV. Fixed 2026-03-08.

## SSH & Deployment

- **Server:** `root@37.27.200.227`, domain `hewasense.majaribio.com`, deploy dir `/opt/hewasense/app/phase2`
- **Compose file:** `docker-compose.dev.yml` (shadow-run profile). Compose is **v2 plugin** (`docker compose`, NOT `docker-compose`).
- **SSH automation key:** `~/.ssh/id_hewasense_auto` (passphraseless). Config: `Host hewasense` → `IdentityFile ~/.ssh/id_hewasense_auto`.
- **What does NOT work on Windows:** bashrc SSH agent, Windows OpenSSH named pipe (`//./pipe/openssh-ssh-agent`), ControlMaster (Unix sockets unsupported in Git Bash).

## Data Assets

- **25-year climate data (real values):** `phase2/data/processed/master_dataset.csv` — 1,878 rows, 6 locations, 2000–2026, unscaled.
- **WARNING:** `phase2/outputs/processed/master_dataset.csv` (server + local) = z-score normalized ML features — NOT for display.
- **Training artifacts:** `outputs/models/latest_training_results.json` — actual test-set metrics from 2026-03-05.

## DB Wipe Recovery Checklist

1. `docker exec climate_backend_dev python init_db.py`
2. `docker exec climate_backend_dev python scripts/seed_users.py`
3. `docker exec climate_backend_dev python scripts/seed_models_and_forecasts.py`
4. SCP `phase2/data/processed/master_dataset.csv` → server `/opt/hewasense/app/phase2/data/processed/`
5. `docker exec climate_backend_dev python scripts/load_climate_data.py --csv /app/data/processed/master_dataset.csv`

## ML Design Decisions

- **Ensemble = Weighted Blending (30% RF / 40% XGBoost / 30% LSTM).** Weights hardcoded, not learned. Ensemble R²=0.840 underperforms XGBoost alone (R²=0.8666) — weaker models drag it down. XGBoost is the primary serving model in practice.
- **Why weighted blending was kept despite lower accuracy:** Regulatory interpretability. A regulator can audit "30/40/30 fixed blend" trivially. A stacked meta-learner raises questions about training data, meta-model overfitting, and auditability that are difficult to answer in a regulated insurance context. Conscious trade-off: interpretability > marginal accuracy gain.
- **Future improvement path:** Once Brier Scores arrive (~Jun 2026), compare calibrated XGBoost (Platt scaling / isotonic regression) vs stacked ensemble vs current blend using forward-validation ground truth — not retrospective R².

## Gitignore Rules (phase2/)

- `memory/` — tracked (removed from gitignore 2026-03-08). Negation patterns `!memory/`, `!memory/logs/`, `!memory/logs/**` override root `.gitignore`'s global `logs/` rule.
- `/logs/` — anchored to root only (pipeline runtime logs). Keeps `memory/logs/` accessible.
- `state.json` — correctly gitignored (Claude Code session state, machine-specific).
- **VS Code gitignore decoration is unreliable.** Always verify with `git ls-files` or `git check-ignore -v`.

## Medium Article

- **File:** `docs/Kilombero Pilot/MEDIUM_ARTICLE_PART_2_FINAL.md`
- **Status:** Final — pending Part 1 URL + pipeline diagram before publish.
- **Balance rule:** Public draft controls disclosure level. Internal draft provides specific numbers (R², feature counts, 6AM EAT, 12 forecasts). Never reveal architecture, thresholds, or internal service names.
- **Pre-publish checklist:** (1) link to Part 1, (2) consistent "I" throughout, (3) explain domain terms, (4) concrete time horizons, (5) non-repetitive conclusion, (6) pipeline diagram (not empty dashboard screenshot), (7) cover image.

## Learned Behaviors

- Always check `tools/manifest.md` before creating new scripts
- Follow GOTCHA framework: Goals, Orchestration, Tools, Context, Hardprompts, Args
- Follow ATLAS build workflow: Architect, Trace, Link, Assemble, Stress-test
- Read `.agent/rules/SKILL.md` on every model activation
- After any model retrain or config change, update ALL docs listed in SKILL.md Law #8
- When quoting accuracy, always specify: model name, dataset (single vs 6-loc), and whether retrospective or forward-validated
- **Never hardcode model filenames** — always use `active_model.json` for dynamic model resolution
- After code changes in volume-mounted containers, **always restart the container** to reload Python modules
- Advisory lock uses dedicated connection (not xact lock) — ORM commits don't affect it
- Always verify feature count at model load time (GOTCHA Law #6: must be 83)
- Use in-memory job store + `misfire_grace_time=1` — prevents phantom duplicate runs after restarts
- ERA5: use `ecmwf-datastores-client` (NOT deprecated `cdsapi`) — the old client had unrecoverable DNS/connection failures

---

*Last updated: 2026-03-08*
*This file is the source of truth for persistent facts. Edit directly to update.*
