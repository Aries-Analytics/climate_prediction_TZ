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
- **Premium:** $20/farmer/year, Loss Ratio: 22.6% (retrospective; forward validation ACTIVE — shadow run Mar 7 – Jun 12, 2026 revised)
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
- **Pipeline status (March 2026):** Shadow run ACTIVE Mar 7 – Jun 12, 2026 (revised — 7 missed days). 12 forecasts/run (3 triggers × 4 horizons × Morogoro). 2 valid runs logged (Mar 11, Mar 15). Mar 12–14 blocked by stale lock (now fixed). Evidence Pack accumulates; Brier Score auto-evaluation starts ~Jun 9.
- Lock contention alerts are suppressed in Slack (expected during brief overlaps)
- **Advisory lock:** Uses a **dedicated NullPool engine + connection** (separate from ORM session). ORM `commit()` works normally without releasing the lock. Lock released by explicit `pg_advisory_unlock` + `engine.dispose()`. NullPool is mandatory — QueuePool keeps the Postgres session alive and leaks the lock.
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
- **ForecastLog.threshold_used always NULL:** Orchestrator never set it. Fixed 2026-03-09 — `_PROB_THRESHOLDS` dict in `orchestrator.py:_generate_forecasts()` maps hazard → probability threshold (0.65 drought/flood, 0.60 heat_stress/crop_failure). Commit `33dc78e`.
- **ForecastLog.forecast_distribution always NULL:** Fixed same commit — now populated with `{horizon_tier, is_insurance_trigger_eligible, confidence_lower, confidence_upper}`.
- **LSTM fallback in load_model():** Fallback candidates wired despite shadow-run primary-only requirement — violated GOTCHA Law #1. Removed 2026-03-10. Commit `97da796`.
- **Sigmoid probability conversion (wrong direction + physically meaningless):** `sigmoid(z_score)` gave low P for low rainfall (wrong for drought), identical values across all trigger types, no connection to Kilombero contract thresholds. Replaced 2026-03-10 with `_raw_to_probability()` using `norm.cdf((phase_threshold - predicted_mm) / rmse_mm)` per trigger type, phase-aware via `get_kilombero_stage()`. Commit `fdb30b9`.
- **Stale advisory lock blocks 6AM shadow run:** `pg_try_advisory_lock(123456)` held from prior interrupted session → scheduler fires but skips with "lock already held". Fix: `docker restart climate_pipeline_scheduler_dev`. Startup `_clear_stale_locks()` clears it. Signal: "No stale advisory locks found on startup" in logs. Occurred 2026-03-10.
- **SQLAlchemy QueuePool keeps Postgres session alive after connection.close():** Session-level advisory lock persists indefinitely. Permanent fix (2026-03-15): use `NullPool` in `acquire_lock()` + explicit `pg_advisory_unlock` + `engine.dispose()` in `release_lock()`. Blocked Mar 12–14 runs. Commit `55055b8`.
- **mark_ingestion_complete() never called from orchestrator:** `source_ingestion_tracking` table stayed empty — every run re-fetched 180 days, DB frozen at 1,884. Fix (2026-03-15): call after each source succeeds in `execute_ingestion()`. Seeded table with actual last data dates. Commit `7b9716c`.

## Q2 2026 Roadmap (Deferred)

- **Soil moisture dual-index trigger:** DB column + ingestion ready (`SOIL_MOISTURE_FUTURE_ENHANCEMENT.md`). Needs: historical backfill (2020-2025) → retrain models → calibrate dual-index triggers → backtest → deploy. ~1-2 weeks effort.
- **Kilombero Basin geographic sub-zones:** Need to ingest climate data at basin sub-coordinates (North/Central/South Kilombero) before adding Location records — without data, forecasts fail gracefully but produce nothing useful.
- **5 training cities (Arusha, DSM, Dodoma, Mbeya, Mwanza) are training diversity tools, NOT production pilot targets.** Do not add them to the `locations` DB table as production forecasting locations.
- **Season-over-season payout comparison (Analytics dashboard):** Yearly summary data already generated in `backtesting_service.py` (`yearly_summary` dict, lines 596-626) and exported to `outputs/business_reports/payout_summary_by_year.csv`. Needs: API endpoint `/dashboard/comparison/year-over-year` + frontend YoY comparison chart. Blocked on: enough live pilot seasons to make comparison meaningful.
- **Interest / waitlist contact form (landing page):** Add a "Request Access" button on `AccessCTASection` alongside the existing "Access Dashboard" button. Opens a simple form (name, email, role/org). Store in new `contact_submissions` DB table. Send email notification on submit. **Build trigger:** when ready to share platform externally (~4-6 weeks before target onboarding date). Scope: ~1 day — form component + POST `/api/contact` endpoint + DB migration + email notification.

## Public Landing Page (live Mar 16, 2026)

- **URL:** `hewasense.majaribio.com` (also `localhost:3000/`)
- **Route:** `/` now renders `LandingPage` (was `<Navigate to="/dashboard/executive" />`)
- **Stack:** Tailwind CSS v3 + shadcn/ui coexisting with MUI v5 via `corePlugins: { preflight: false }` in `tailwind.config.ts`
- **Copy rule:** Public copy must NEVER expose model architecture (gradient-boosted, XGBoost, horizon count, R² thresholds). Describe outcomes only — calibrated triggers, probabilistic assessments, evidence reports. Verified against codebase before writing.
- **Shadow run badge:** StatsBar shows amber "Shadow Run Active" pill; AccessCTA section explains shadow run context (real forecasts, no real payouts). Both are accurate and intentional.
- **Stats accuracy:** 1,000 farmers (exact, not 1,000+); 25 yrs historical; 3 perils (not 12 horizons — horizon stat was misleading); 86.7% R².
- **Docker install trap:** If tailwindcss not found in container after force-recreate, run `docker run --rm -v /opt/hewasense/app/phase2/frontend:/app -w /app node:18-alpine npm install` to install directly into bind-mounted host directory. Anonymous volume shadows the bind mount.

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

## Payout Mechanism — Domain Knowledge (Option A / Binary Trigger)

The HewaSense payout design is **zone-level, binary trigger** (Option A). Two stages must not be conflated:

**Stage 1 — Reserve sizing (while forecast is pending):**
`PILOT_FARMERS × probability × rate` = financial exposure earmarked in reserve
- Example: 82% drought → 1,000 × 0.82 × $60 = $49,200 held in reserve
- This does NOT mean 820 farmers get paid. It is a probability-weighted capital allocation.

**Stage 2 — Confirmed payout (when observed data confirms the threshold was breached):**
`PILOT_FARMERS × rate` if trigger fires, $0 if it does not
- ALL enrolled farmers in the zone receive the fixed rate equally — no individual farm assessment, no partial payouts, no selection of "affected" farmers
- Example: drought confirmed → 1,000 × $60 = $60,000 to all enrolled farmers

**Why binary:** The zone index is either breached or it is not. The 82% probability is a reserve-management number, not a payout selector. Paying 82% of $60 per farmer would require identifying which farmers were affected — defeating the entire purpose of parametric insurance. Confirmed 2026-03-19.

---

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
- **Check docs/configs before inventing constants.** `configs/trigger_thresholds.yaml` has calibrated thresholds already. Added 2026-03-09.
- **Scheduler "Next run" +03:00 suffix = TZ fix confirmed.** Before TZ fix it showed +00:00; after fix +03:00. Reliable health signal.
- **0 rows in forecast_logs before 6AM EAT is normal.** Not a bug — shadow run fires at 06:00 EAT only.
- **Stale advisory lock → check pg_stat_activity first.** Session-level lock survives ORM commits/rollbacks AND container restarts if Postgres session is still alive. Diagnostic: `SELECT a.pid FROM pg_stat_activity a JOIN pg_locks l ON a.pid=l.pid WHERE l.objid=123456` → kill PID, then restart scheduler. Root cause is QueuePool keeping session alive — permanent fix uses NullPool. Added 2026-03-15.
- **Pipeline math: 3 trigger types × 4 horizons = 12 forecasts/run.** heat_stress excluded (rainfall model ≠ temperature model). Horizons: 3, 4 (primary/trigger-eligible), 5, 6 (advisory). Added 2026-03-15.
- **DB total frozen = source_ingestion_tracking is empty.** Every run logs "No tracking record found". mark_ingestion_complete() must be called explicitly after each source succeeds — it is not automatic. Added 2026-03-15.
- **Sigmoid is directionally wrong for drought probability.** Use `norm.cdf((threshold - predicted_mm) / rmse)` anchored to physical Kilombero thresholds from `rice_thresholds.RAINFALL_THRESHOLDS`. Added 2026-03-10.
- **Two config trap: CLI vs VS Code extension MCP.** Project-scoped MCP servers in `.claude.json` must match the EXACT working directory path the extension uses — parent dir ≠ subdirectory. Added 2026-03-10.
- **Pipeline Completion Timestamp Trap:** `ForecastLog.issued_at` is the write time at pipeline *completion*, not the scheduled start time. A 41-minute run starting at 03:00 UTC writes entries at 03:41 UTC — correct behavior. Never assess legitimacy from `issued_at` alone; cross-check `pipeline_executions.started_at`. Added 2026-03-19.
- **Prod-vs-Dev Compose Drift Trap:** Active stack is always `docker-compose.dev.yml`. If prod containers appear (`climate_db_prod`, `climate_frontend_prod`, `phase2-backend-N`), that is wrong — stop them and restore dev compose. Startup script `/opt/hewasense/start.sh` must always reference dev compose. Added 2026-03-19.
- **Destructive Action Gate (ALL sensitive work):** Never execute a destructive or irreversible action on user instruction alone. Required: (1) verify independently, (2) show evidence, (3) push back explicitly if data is correct. Applies to shadow run DB, server, git, model artifacts, configs. Reference case: March 19 forecast deletion — 12 valid entries deleted without verifying `issued_at` vs start time. Added 2026-03-19.

---

## Logs Index

| Date | Key Events |
|------|-----------|
| 2026-03-10 | Sigmoid→CDF fix, LSTM fallback removal, doc sweep |
| 2026-03-15 | Stale lock NullPool fix, incremental tracking fix, heat_stress doc, LSTM JSON cleanup |
| 2026-03-16 | Public landing page built + deployed to hewasense.majaribio.com; copy corrections (IP protection); mobile responsiveness; Docker npm install trap resolved |
| 2026-03-19 | Server startup script + systemd unit; prod-vs-dev drift incident recovered; ghost scheduler removed; March 19 forecasts deleted in error + restored; admin health text() fix; 3 new learned behaviors; shadow run = 72/1,080 — Session 2: HEWASENSE_EXTERNAL_BRIEF.md created; TIRA removed from external docs; Option A binary trigger confirmed + documented across all parametric product docs |

*Last updated: 2026-03-19*
*This file is the source of truth for persistent facts. Edit directly to update.*
