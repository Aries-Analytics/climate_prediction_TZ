# Persistent Memory

> This file contains curated long-term facts, preferences, and context that persist across sessions.
> The AI reads this at the start of each session. You can edit this file directly.

## Project Overview

- **Project:** HewaSense — Climate intelligence for parametric crop insurance (Tanzania)
- **Framework:** GOTCHA (6-layer) + Compound Engineering workflow (/ce:brainstorm → plan → work → review → compound) + 4-Persona model
- **Current Phase:** Shadow-Run Forward Testing (Phase 4.0)
- **Pilot:** Kilombero Basin (Ifakara TC + Mlimba DC), 1000 rice farmers (400 + 600 split)
- **Production Model:** Phase-Based Dynamic Model (4-phase GDD tracker)

## Key Facts

- **Production ML Model:** XGBoost, Test R²=0.8666 (86.7%) — primary serving model (post data leakage fix, 11 rainfall-derived features removed)
- **Ensemble R²:** 0.8402 (secondary model, not used for forward predictions)
- **98.4%/98.3%:** Single-location/older dataset benchmarks — historical only, NOT the production number
- **Basis Risk:** 20% (Phase-Based Dynamic Model) — production. 10% (April threshold) — baseline only.
- **Phase-Based Model:** Catches 100% of confirmed crop disasters (2017/2018 and 2021/2022), zero false negatives
- **Premium:** $20/farmer/year, Loss Ratio: 22.6% (retrospective; forward validation ACTIVE — shadow run Apr 14 – Jul 13, 2026, restarted for two-zone split)
- **HewaSense Engine V4 (Feb 2026):** Dynamic GDD tracking, cumulative flood limits (120-160mm over 5 days)
- **Out-of-Sample Validation:** 9.6% historic loss ratio (2000-2014)
- **Spatial Validation:** CHIRPS 5km grid correlated at r=0.888 against local gauges
- PILOT_LOCATION_IDS = [7, 8] (7 = Ifakara TC @ -8.1333, 36.6833; 8 = Mlimba DC @ -8.0167, 35.9500). Old location_id=6 (Morogoro city) deprecated — coordinates were 120+ km from actual Kilombero Basin.
- Payout threshold = 75%
- Models expect **83 features** (retrained Mar 2026; 11 leaky rainfall-derived features removed from 279, leaving 245 candidates; 83 selected)
- Feature schema: `feature_selection_results.json` (83 features, single source of truth)
- Law #8 (AUTONOMOUS DOCUMENTATION) mandates doc updates after any model/config change
- **Production model file:** Determined by `outputs/models/active_model.json` (currently `xgboost_climate.pkl`, R²=0.8666, 83 features). NEVER hardcode model names
- Model selection driven entirely by `active_model.json` — if missing or invalid, fail explicitly (GOTCHA Law #1)
- **Pipeline schedule (shadow-run ACTIVE):** `0 6 * * *` Africa/Dar_es_Salaam (6 AM EAT daily). Deployed to `root@37.27.200.227`, `docker-compose.dev.yml`. Scheduler confirmed next run `2026-03-09 06:00:00+03:00`.
- **Pipeline status (April 2026):** Shadow run v2 RESTARTED Apr 16 – Jul 14, 2026 (two-zone split: Ifakara TC + Mlimba DC). 24 forecasts/run (3 triggers × 4 horizons × 2 zones). Target: 2,160 forecasts over 90 run-days. Brier Score auto-evaluation starts ~Jul 11. v2 (Apr 14-15) invalidated — stale ingestion modules stored climate data at Morogoro coordinates instead of pilot zones, producing only 12 forecasts/day from wrong location. DB wiped, config restarted. **Live counts (forecasts accumulated, run-days, streak) are in the Evidence Pack dashboard — do NOT read from memory.**
- **Zone-split evaluation layer (Apr 14, 2026):** All metrics, basis risk, GO/NO-GO gates, and evidence pack are now per-zone (Ifakara TC + Mlimba DC) + aggregate. API endpoints `/metrics` and `/basis-risk` accept `?location_id=7` or `?location_id=8` for zone-specific views. Final report has per-zone gate verdicts nested under overall. Evidence pack `metrics.json` includes `zones` dict; `logs_export.csv` has `zone_name` column. PILOT_ZONE_IDS = [7, 8] defined in `evaluation_service.py`, imported by `basis_risk_service.py`. Execution-log endpoint returns structured zone objects from DB (not hardcoded strings).
- **Frontend zone-aware dashboard (Apr 14, 2026):** EvidencePackDashboard fully rewritten with zone tabs, basis risk display, GO/NO-GO gate rendering, and per-zone metrics. All zone names/coordinates/counts are data-driven from API responses. ForecastDashboard `kilomberoLocations` hardcoded array replaced with dynamic fetch from `/api/locations`, filtered to locations that appear in actual forecast data.
- **Shadow run config — single source of truth (Apr 14, 2026; updated Apr 16):** All shadow run parameters (start date, target days, target forecasts, end date) live in `app/config/shadow_run.py`. Imported by orchestrator, auto_log_service, alert_service, evidence_generator, evidence.py, admin.py. To restart a shadow run with new dates, change ONLY that file. All forecast_log queries filter by `>= SHADOW_RUN_START` to prevent stale data from inflating counts. Post-shadow-run evaluation (Stage 4 → Stage 5 → generate_final_report) is fully zone-aware and automatic.
- Lock contention alerts are suppressed in Slack (expected during brief overlaps)
- **Advisory lock:** Uses a **dedicated NullPool engine + connection** (separate from ORM session). ORM `commit()` works normally without releasing the lock. Lock released by explicit `pg_advisory_unlock` + `engine.dispose()`. NullPool is mandatory — QueuePool keeps the Postgres session alive and leaks the lock.
- **Scheduler job store:** In-memory (NOT persistent SQLAlchemyJobStore). Prevents phantom runs from stale `next_run_times` after container restarts.
- Scheduler clears stale advisory locks on startup (`_clear_stale_locks()` terminates old PostgreSQL backends)
- Forecast lookback: **12 months** + `.replace(day=1)` to ensure ≥6 monthly records (updated Mar 21; was 7 months earlier)
- **ML normalization constants (production):** Training distribution mean = 79.15mm, std = 77.06mm. Inverse transform: `predicted_mm = (z_score × 77.06) + 79.15`. XGBoost RMSE = 33.1mm (used as σ in CDF probability conversion).
- **ERA5 client:** `ecmwf-datastores-client` (v0.4.2) — migrated from deprecated `cdsapi` which had connection/DNS failures. New client uses `ECMWF_DATASTORES_URL`/`ECMWF_DATASTORES_KEY` env vars.
- **No synthetic data fallbacks** (GOTCHA Law #1): if critical data sources fail, forecasts are skipped — never filled with zeros

## Documentation Tone (Expert Feedback — March 2026)

- **Never use "production-ready"** → use "pilot-ready" or "forward validation phase"
- **Always qualify accuracy numbers** with dataset context (single-location vs 6-location)
- **Include Known Limitations** in all externally-facing docs
- **Yield ground truth (updated 2026-04-13, 4 sources — TWO-ZONE BASELINES):** Recalibrated from Kilombero District Council data (2020/21–2024/25, Mlimba DC + Ifakara TC). **Zone baselines:**
  - **Ifakara TC:** 2.30 MT/Ha (5yr avg, CV 11.9%, volatile/flood-prone). Loss trigger: 1.38 MT/Ha (40% below).
  - **Mlimba DC:** 2.59 MT/Ha (5yr avg, CV 3.5%, stable). Loss trigger: 1.55 MT/Ha (40% below).
  - **Combined district:** 2.53 MT/Ha (supersedes old 2.099 triangulated baseline).
  - Old triangulated sources (MapSPAM, HarvestStat, World Bank) kept as secondary references in `data/external/ground_truth/`.
  - New primary source: `data/external/ground_truth/kilombero_district_rice_yield_2020_2025.csv` (from Kilombero District Council via Walter, Apr 13 2026).
  - ILRI NAFAKA (restricted) — still blocked, author contact: Charles Joseph Chuwa, ARI-Dakawa.
- **Data resolution:** CHIRPS (5km) vs NASA POWER (50km) mismatch documented, mitigation planned (rain gauges)
- **Historical reports** in `docs/reports/` and `docs/archive/` are never modified

## GOTCHA Layer Locations

- Goals: `goals/manifest.md` → individual goal files
- Tools: `tools/manifest.md` → scripts index
- Context: `context/` → domain knowledge
- Hard Prompts: `hardprompts/` → templates
- Args: `args/persona_config.yaml`

## Domain Knowledge — Stats, Framing & Numbers

- **"610 events" framing (corrected Mar 20):** The 610 are location-month-peril threshold exceedances across 6 locations × 3 peril types × 26 years (1,872 total records) — NOT 610 independent farmer crisis episodes. Do NOT present as "610 farmers affected." The corrected external framing: *"Across six locations and three peril types, thresholds were breached an average of 23.5 times per year — meaning smallholders face multiple distinct climate hazards each season with no financial safety net."* The individually defensible actuarial numbers for decks are per-peril trigger rates: **Drought 12%, Flood 9.3%, Crop Failure 6.2%**.
- **Loss ratio — Morogoro vs 6-location (Mar 20):** The 22.6% retrospective loss ratio is **Morogoro (single-location) pilot calibration**. The $1,590/yr payout aggregate spans ALL 6 training locations — dividing this by the Morogoro single-location premium (~$1,988/yr) yields ~80%, which is a multi-location scale artefact, not a real discrepancy. The 75% Morogoro loss ratio comes from iterating thresholds against 26 years of Morogoro data specifically. Never conflate or do cross-scale arithmetic between these figures. Clarifying note is in `PARAMETRIC_INSURANCE_FINAL.md`, `HEWASENSE_EXTERNAL_BRIEF.md`, and `BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md`.
- **Correlation clustering in reserve sizing (Mar 20):** Region-wide drought or flood triggers correlated payouts across all enrolled zones simultaneously. Reserve sizing must use a **joint exceedance probability** (not independent zone probabilities summed). A single correlated event can exhaust reserves sized for uncorrelated risk. This is documented in the actuarial model but must be noted in all reserve discussions.
- **Loss ratio disambiguation (Apr 2):** Two distinct figures must not be conflated: (1) **Actuarial retrospective** = 22.6% (historical analysis, Morogoro, 6 seasons). (2) **Forward stress test** = percentage under active shadow run with current trigger probabilities. Dashboard must show both separately with labels.
- **5-7 day payout timing confirmed (Mar 31):** From trigger confirmation to farmer wallet credit, the SLA is 5-7 business days. This is the committed metric for investor/partner materials.

## ML Reference — Inference Chain & Model Context

- **Inference chain (ML_MODEL_REFERENCE v3.6, Mar 21):** Weather input → feature engineering (83 features) → XGBoost prediction (monthly mm equivalent) → `_raw_to_probability()` using `norm.cdf((phase_threshold - predicted_mm) / rmse_mm)` per trigger type → trigger eligibility gate (horizon must be 3 or 4) → advisory tier (horizons 5-6, no payout). This chain is the canonical path — do NOT shortcut or substitute steps.
- **CDF rationale (Mar 21):** The CDF (cumulative distribution function) converts a point prediction to a probability of breaching the physical threshold. It is **not** a model confidence score — it answers "given the predicted rainfall level and model uncertainty, what is the probability the actual outcome falls below the trigger threshold?" Uses normal CDF with RMSE as σ. Physical Kilombero thresholds from `configs/trigger_thresholds.yaml`.
- **ML frontier positioning (Mar 21):** HewaSense is positioned as **probabilistic trigger** (not binary threshold). Traditional WII uses static historical percentiles; HewaSense uses live ML-generated probability with phase-aware physical thresholds. This distinction matters for investor/regulator framing — it is a more sophisticated and defensible trigger mechanism.
- **3-phase improvement roadmap (Mar 21, post-Brier):** Phase 1 = Brier Score validation (Jun 2026, current). Phase 2 = Platt scaling / isotonic regression on XGBoost outputs using forward-validation ground truth. Phase 3 = stacked ensemble re-evaluation using calibrated components. Do not jump to Phase 2/3 until Phase 1 data exists.
- **Horizon decision gate (Mar 21):** Horizons 3 and 4 are trigger-eligible (actionable lead time for insurance purposes). Horizons 5 and 6 are advisory only — too uncertain for binding payout commitment. This gate is enforced in `orchestrator.py`.
- **Pitch deck integrity review (Mar 30):** Review confirmed: (1) R² must always include dataset qualifier; (2) "zero false negatives on confirmed disasters" refers specifically to 2017/18 and 2021/22 — state the reference events explicitly; (3) basis risk claim requires corroborating evidence (NDVI signal, cooperative reports) before being stated definitively in external materials.

## Business Development

### BimaLab Accelerator Arc
- **Mar 19 (deferred):** Decision made to wait until Brier Scores available (~Jun 2026) before applying. Rationale: accelerator panels ask hard questions about forecast accuracy; Brier Scores provide the forward-validation proof needed to answer credibly.
- **Mar 27 (outreach sent):** Application/outreach submitted. Status: **warm lead active**.
- **Target:** Q3 2026 cohort.
- **"1,000 farmers" framing (Mar 27):** Use **exactly "1,000 farmers"** in all external materials during shadow run — not "1,000+" or "growing". Only upgrade to dynamic framing when live onboarding of additional farmers begins. Premature scaling language damages credibility if challenged.

### Three-Scenario Pricing Model (Mar 22)
- **Scenario A — No subsidy (base case):** $20/farmer/year. Full cost to farmer. Loss ratio 22.6%. $60 payout per trigger.
- **Scenario B — Donor/NGO co-funded:** ~$12/farmer/year. Donor/NGO covers delta. Target: AGRA, GSMA, WFP-type programs.
- **Scenario C — Government MOU:** ~$10/farmer/year. Government absorbs premium subsidy in exchange for data rights / district-level reporting.
- Use Scenario A as default in all financial projections. B and C require signed MOU/grant confirmation before inclusion in cap table or financial model.

### Tabora Tobacco Expansion (scoped Mar 22)
- **ACRE/NBC WII live product confirmed:** Acre Africa + NBC (National Bank of Commerce) already have a live weather-indexed insurance product for Tanzanian smallholders. This is a reference product — validates market exists.
- **TAIC payout history:** Tanzania Agricultural Insurance Consortium has paid out TZS 3 billion+ in crop insurance. Market precedent established.
- **TTB distribution channel:** Tanzania Tobacco Board controls all registered tobacco farmers (mandatory registration). Single channel to reach ~300,000 smallholder tobacco growers in Tabora/Urambo/Igunga.
- **IFC/WB capital exclusion:** IFC and World Bank financing instruments explicitly exclude tobacco under social/environmental safeguards. Do NOT pursue tobacco expansion using IFC/WB-linked funding — scope only with private capital or DFIs without tobacco exclusion clauses.
- **Pre-conditions for Tabora expansion:** (1) Shadow run complete + Brier Scores validated; (2) TIRA pilot license issued; (3) Private/non-IFC funding confirmed; (4) TTB formal partnership MOU; (5) At minimum 1 full season HewaSense tobacco trial data.

### Basis Risk Strategy (Mar 30)
- **Definition of basis risk in this context:** The risk that the parametric trigger fires but the farmer's actual loss was not real (false positive), OR the trigger does NOT fire but actual loss occurred (false negative).
- **5 proxy evidence paths identified (Mar 30) to demonstrate basis risk control:**
  1. **NDVI correlation** — MODIS NDVI vs trigger outcomes. If drought trigger fires and NDVI shows vegetation stress in same direction, basis risk is reduced.
  2. **Kilombero cooperative yield reports** — Harvest reports from Kilombero Valley Teak Company / rice cooperatives as independent ground truth.
  3. **ACRE Africa loss adjustment surveys** — Reference data from Acre's existing programs for triangulation.
  4. **FAOSTAT district-level** — When available, compare trigger year against Tanzania NBS district production data.
  5. **Farmer self-report via USSD/SMS** — Post-season structured survey (simple harvest above/below average binary) to collect qualitative corroboration. Cheap, scalable.
- **NDVI first signal (Mar 30):** Drought probability 0.53 (elevated but below trigger threshold) + NDVI delta -0.031 (monitoring, not alarming) — both indicate **same direction** of stress. This is the first observed basis risk corroboration data point in the shadow run. Document each instance.

### Kilombero Cooperative Contacts (harvested Mar 30)
- **Anthony Mhagama (IUCN):** Warm introduction door to Kilombero Valley rice cooperative leadership. IUCN has active conservation programs in the Kilombero floodplain — approach through Anthony for formal cooperative engagement.
- **Note:** Specific phone numbers and named contacts were in deleted session logs (commit `a8a5d2e`). Full contact details must be re-sourced from original outreach records or Anthony's referral chain. This is a known gap from log deletion.

## External Communications & Documents

- **External Brief:** `docs/references/HEWASENSE_EXTERNAL_BRIEF.pdf` (created Mar 19). This is the primary investor/partner-facing document. Internal founders context must NEVER be transcribed directly — extract the insight, rebuild around the audience's question.
- **TIRA removal (Mar 19):** Tanzania Insurance Regulatory Authority (TIRA) was removed from the external brief. Reason: premature to name the regulator before formal engagement — creates expectation of approval that does not yet exist. Reference only as "subject to relevant regulatory approvals."
- **Terminology rule — external materials:** Use **"forward validation run"** (not "shadow run"). "Shadow run" is an internal technical term; "forward validation" communicates scientific rigor to external audiences without implying the system is non-operational.
- **Public copy rule (confirmed Mar 16/19):** Never expose model architecture, XGBoost, gradient-boosted, horizon count, R² thresholds, or internal service names in external materials. Describe outcomes only: calibrated triggers, probabilistic assessments, evidence reports.

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
- **NASA POWER partial-month NaN ingestion:** `end_date = datetime.now(timezone.utc)` with no month cap fetched current partial month (e.g. April 1 = 1 day of data) → stored as NaN temperature/solar. Stale row deleted. Fix (2026-04-01): cap `end_date` to last complete month end using `now_utc.replace(day=1) - timedelta(days=1)`. Commit `a4bfe9b`.
- **CHIRPS partial-month silent corruption:** No month cap → partial month `.sum()` returns a real value (~80% too low) — NOT NaN, silently wrong. Fix (2026-04-01): same last-complete-month cap pattern in `ingest_chirps()`. Commit `11faebd`.
- **NDVI partial-month misrepresentation:** No month cap → monthly aggregate from only first 16-day MODIS composite misrepresents full-month vegetation state. Fix (2026-04-01): same cap pattern in `ingest_ndvi()`. Commit `11faebd`.
- **ERA5 MARS AccessError -2 (ERA5T restricted access):** `ingest_era5()` last-complete-month cap allowed Feb–Apr 2026 through — these fall in ERA5T (near real-time, <3 months old) which requires a separate restricted subscription. Fix (2026-04-03): replaced cap with `ERA5_LAG_MONTHS=3` boundary; added `end_month=` param to `fetch_era5_data()` so month list never overshoots. Commit `8cd03a3`.
- **Auto-log git push rejected (non-fast-forward):** Stage 6 runs at 06:00 EAT; `/log-session` commits pushed after that leave server repo behind remote → next morning push fails. Fix (2026-04-03): added `git pull --rebase origin phase2/feature-expansion` between commit and push in `_git_commit_and_push()`. Non-blocking on rebase failure. Commit `8cd03a3`.
- **Off-season forecasts appearing as active payout triggers:** `GET /climate-forecasts/alerts` had no crop calendar filter — August drought at 88% (4-month horizon, dry season peak) surfaced as a payout trigger despite no insured crop in the field. Fix (2026-04-02): `continue` guard after `get_kilombero_stage()` returns `off_season` in `climate_forecasts.py`. Commits `e2c649f`.
- **Wrong `PREMIUM_PER_FARMER = 91`:** Stale value from old backtesting scenario. Pilot premium is $20/farmer/year (Scenario A). Was inflating `total_premium_income` to $91,000 and underreporting loss ratio as 114.7% instead of correct 200% cap. Fix (2026-04-02): corrected to `20`. Commit `67aa269`.
- **Dashboard conflating Stage 1 reserve sizing with confirmed payout trigger:** "1 active payout trigger", red error banner, enabled "Approve Payout Batch" button — all misleading during shadow run with 0mm observed deficit. Fix (2026-04-02): language relabeled to forecast alerts, PayoutActionCard locked with `shadowRunActive` prop, loss ratio split into actuarial vs forward stress. Commits `67aa269`, `e2c649f`, `9a48130`.
- **Partial-month cap: tz-naive vs tz-aware TypeError (Apr 6):** `last_complete_month_end` built from `datetime.now(timezone.utc)` → tz-aware pandas Timestamp; `end_date` stripped to tz-naive. Comparison `end_date > last_complete_month_end` throws `TypeError`. Affected chirps, nasa_power, ndvi (all 3 added the cap on Apr 1). ERA5 unaffected — it normalises `end_date` to UTC-aware before comparison. Only triggered Apr 6 — first day incremental manager returned a current-month end_date. Fix (2026-04-06): replaced `now_utc = datetime.now(timezone.utc)` + tz-aware `pd.to_datetime` with `_today = date.today()` + `date(_today.year, _today.month, 1) - timedelta(days=1)`. Added missing `date` import to nasa_power and ndvi. Commit `40b1bc7`.
- **ERA5: date vs datetime TypeError (Apr 7):** `era5_ingestion.py` used `hasattr(end_date, 'tzinfo')` to detect if `end_date` needed tz normalisation before comparing against `era5_safe_end` (tz-aware `datetime`). Plain `date` objects (from incremental manager) have no `tzinfo` attribute — `hasattr` returned `False`, normalisation skipped, `date > datetime` raised `TypeError`. Different bug from Apr 6 (same symptom family, different type pair). Fix (2026-04-07): replaced `hasattr` guard with `isinstance(end_date, datetime)` — if plain `date`, promote via `datetime.combine(end_date, time.min).replace(tzinfo=UTC)`. Added `time` to imports. Commit `c77be7a`.

- **ERA5: monthly filter tz mismatch + month-boundary exclusion (Apr 9):** After the Apr 7 fix promoted `end_date` to a UTC-aware datetime, the final monthly pandas filter compared tz-naive `df["date"]` values against a tz-aware `end_date`, raising `Invalid comparison between dtype=datetime64[ns] and Timestamp` on the Apr 8 run. Local repro also showed a second issue: even without the exception, the monthly January row (`2026-01-01`) would be excluded because the incremental window started on `2026-01-08`. Fix (2026-04-09): in `modules/ingestion/era5_ingestion.py`, strip timezone info from the pandas bounds after the ERA5 lag cap and normalize both bounds to month-start timestamps before filtering. Commit `4948306`. Deployed to `root@37.27.200.227`; `pipeline-scheduler` restarted healthy and scheduled next run `2026-04-09 06:00:00+03:00`.

## Known Bugs Fixed (Apr 2026)

- **Slack alert "Shadow Run: N/A" (Apr 15):** `alert_service.py` queried `ForecastLog.created_at` — a column that doesn't exist on the model (only `issued_at`). Query threw an exception, caught silently, `forecast_log_count` stayed `None`, Slack displayed "Shadow Run: N/A". Fix: changed to `ForecastLog.issued_at` (matching `auto_log_service.py`).
- **Evidence Pack "Days Completed" showing 1 instead of 2 (Apr 15):** Frontend calculated days as `Math.round(total_forecast_logs / forecasts_per_day)` — integer division (24/24=1). Fix: backend `/execution-log` endpoint now returns `valid_run_days` (count of distinct calendar dates with forecast logs, filtered by `SHADOW_RUN_START`) and `target_days`. Frontend uses API value directly instead of deriving it.
- **Evidence Pack total_forecast_logs unfiltered (Apr 15):** `/execution-log` counted ALL ForecastLog rows with no date filter. Correct but fragile — if DB isn't perfectly wiped, stale logs inflate counts. Fix: added `WHERE issued_at >= SHADOW_RUN_START` filter (matching `auto_log_service.py` pattern).
- **DB wipe script (Apr 14):** `scripts/wipe_shadow_run_data.py` — wipes forecast_logs, pipeline_executions, ndvi_observations, data_quality_metrics, source_ingestion_tracking. Preserves climate_data and locations. Dry-run by default, `--confirm` for live wipe.
- **12 forecasts/day instead of 24 — stale ingestion modules (Apr 15):** Docker-compose mounted `./modules:/app/modules:ro` for the scheduler container, but the two-zone PILOT_LOCATIONS update (commit `6a4f32b`) only updated `backend/modules/ingestion/` — the top-level `phase2/modules/ingestion/` was left with hardcoded Morogoro coordinates (-6.8211, 37.6595). All 5 ingestion sources stored climate data at the wrong location; `forecast_service.py` found no climate data within ±0.01° of the actual pilot zone coordinates. Fix: consolidated both copies into `backend/modules/` only, removed top-level `phase2/modules/` and `phase2/utils/` duplicates, removed explicit docker-compose volume mounts (scheduler now uses `backend/modules` via the existing `./backend:/app` mount). Shadow run wiped and restarted as v3 from Apr 16.
- **Duplicate module directories consolidated (Apr 15):** `phase2/modules/` and `phase2/utils/` DELETED. Single source of truth is now `phase2/backend/modules/` and `phase2/backend/utils/`. Docker-compose.dev.yml no longer has `./modules:/app/modules:ro` or `./utils:/app/utils:ro` mounts — the `./backend:/app` mount handles everything.

## Q2 2026 Roadmap (Deferred)

- **Docs Phase B restructure (post-June gate):** Phase A complete (Apr 7 — empty files deleted, reports archived, pilots/ and validation/ folders created). Phase B deferred to post-shadow-run. Actions: (1) merge 3 pipeline status docs → `current/PIPELINE_CURRENT_STATUS.md`; (2) merge `CLAIMS_MANAGEMENT_DASHBOARD_SPEC.md` → `FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md`; (3) create `domains/` for parametric insurance + climate science materials; (4) create `devops/` for GOTCHA framework + deployment + monitoring; (5) reorganise `archive/phase3/` (79 flat files) by topic; (6) extract HewaSense PDF guides to markdown; (7) merge `BACKTESTING_SUMMARY.md` + `v2.md` into single file. See `docs/archive/_INDEX.md` for full Phase B plan.
- **Soil moisture dual-index trigger:** DB column + ingestion ready (`SOIL_MOISTURE_FUTURE_ENHANCEMENT.md`). Needs: historical backfill (2020-2025) → retrain models → calibrate dual-index triggers → backtest → deploy. ~1-2 weeks effort.
- **Kilombero Basin geographic sub-zones:** Need to ingest climate data at basin sub-coordinates (North/Central/South Kilombero) before adding Location records — without data, forecasts fail gracefully but produce nothing useful.
- **5 training cities (Arusha, DSM, Dodoma, Mbeya, Mwanza) are training diversity tools, NOT production pilot targets.** Do not add them to the `locations` DB table as production forecasting locations.
- **Season-over-season payout comparison (Analytics dashboard):** Yearly summary data already generated in `backtesting_service.py` (`yearly_summary` dict, lines 596-626) and exported to `outputs/business_reports/payout_summary_by_year.csv`. Needs: API endpoint `/dashboard/comparison/year-over-year` + frontend YoY comparison chart. Blocked on: enough live pilot seasons to make comparison meaningful.
- **Interest / waitlist contact form (landing page):** Add a "Request Access" button on `AccessCTASection` alongside the existing "Access Dashboard" button. Opens a simple form (name, email, role/org). Store in new `contact_submissions` DB table. Send email notification on submit. **Build trigger:** when ready to share platform externally (~4-6 weeks before target onboarding date). Scope: ~1 day — form component + POST `/api/contact` endpoint + DB migration + email notification.

## Evidence Pack Dashboard (built Mar 16)

- **Shadow run progress card:** Shows current run-day count, forecasts accumulated, percentage toward 90-day target. Feeds from `pipeline_executions` table.
- **Execution history table:** Full per-run record — date, sources ingested, forecast count, duration, status. Replaces the deleted session logs as pipeline run history. Source of truth: `/v1/evidence-pack/execution-log`.
- **Pipeline records analysis (Mar 16):** Investigation found 24 run attempts → 24 executions logged → only 3 with valid forecasts. Root cause: early runs completed ingestion but hit errors before forecast generation. Ingestion and forecast counts are separate metrics — a "completed" run can have 0 forecasts if the forecast generation stage fails.
- **archive flag (Mar 16):** Jan 2026 docs in `docs/` marked with `archive: true` in frontmatter. These are pre-shadow-run snapshots — never modify, never reference as current state.

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
- **Server startup script (created Mar 19):** `/opt/hewasense/start.sh` — pulls latest from git, runs `docker compose -f docker-compose.dev.yml up -d`. Must always reference `docker-compose.dev.yml` (NOT prod compose). Hardcoded to dev profile.
- **systemd unit (created Mar 19):** `/etc/systemd/system/hewasense.service` — `ExecStart=/opt/hewasense/start.sh`, `Restart=on-failure`, `WantedBy=multi-user.target`. Enabled via `systemctl enable hewasense`. Ensures auto-restart on server reboot without manual intervention.
- **psql trap antipattern (Mar 16):** `psql -U postgres` or `psql -U climate_user` inside `climate_db_dev` → `FATAL: role does not exist` — those roles don't exist; username is in `DATABASE_URL`. Correct method for ad-hoc DB inspection:
  ```bash
  docker exec climate_backend_dev python3 -c "
  from app.core.database import SessionLocal
  db = SessionLocal()
  # SELECT queries only
  db.close()
  "
  ```
  The ORM picks up `DATABASE_URL` from the container environment automatically. Never mutate via ad-hoc psql — use a migration script with rollback plan.

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

- `memory/` — tracked (removed from gitignore 2026-03-08). `memory/logs/` removed 2026-04-03 (pipeline run history moved to DB + Evidence Pack dashboard).
- `/logs/` — anchored to root only (pipeline runtime logs).
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
- Follow Compound Engineering workflow: /ce:brainstorm → /ce:plan → /ce:work → /ce:review → /ce:compound (plugin: compound-engineering v2.61.0)
- Read `.agent/rules/SKILL.md` on every model activation
- After any model retrain or config change, update ALL docs listed in SKILL.md Law #8
- When quoting accuracy, always specify: model name, dataset (single vs 6-loc), and whether retrospective or forward-validated
- **Never hardcode model filenames** — always use `active_model.json` for dynamic model resolution
- After code changes in volume-mounted containers, **always restart the container** to reload Python modules
- **Stage 6 auto-log is a structured log line only.** No files written, no git ops. Pipeline run history is in `pipeline_executions` DB table → Evidence Pack dashboard. Session notes go to external Claude memory via `/log-session`.
- **Shadow run completion automation (built Mar 31):** Stage 5 now detects day-90 completion automatically. On detection: calls `generate_final_report()` → writes final Evidence Pack → triggers `basis_risk_service.py` analysis → sends Slack alert with summary. No manual intervention required at Jun 12 close.
- **basis_risk_service.py (created Mar 31):** Computes basis risk metrics at shadow run completion — cross-references trigger events against NDVI signals and any available cooperative yield reports. Output feeds the final Evidence Pack report.
- Advisory lock uses dedicated connection (not xact lock) — ORM commits don't affect it
- Always verify feature count at model load time (GOTCHA Law #6: must be 83)
- Use in-memory job store + `misfire_grace_time=1` — prevents phantom duplicate runs after restarts
- ERA5: use `ecmwf-datastores-client` (NOT deprecated `cdsapi`) — the old client had unrecoverable DNS/connection failures
- **Check docs/configs before inventing constants.** `configs/trigger_thresholds.yaml` has calibrated thresholds already. Added 2026-03-09.
- **Scheduler "Next run" +03:00 suffix = TZ fix confirmed.** Before TZ fix it showed +00:00; after fix +03:00. Reliable health signal.
- **0 rows in forecast_logs before 6AM EAT is normal.** Not a bug — shadow run fires at 06:00 EAT only.
- **Stale advisory lock → check pg_stat_activity first.** Session-level lock survives ORM commits/rollbacks AND container restarts if Postgres session is still alive. Diagnostic: `SELECT a.pid FROM pg_stat_activity a JOIN pg_locks l ON a.pid=l.pid WHERE l.objid=123456` → kill PID, then restart scheduler. Root cause is QueuePool keeping session alive — permanent fix uses NullPool. Added 2026-03-15.
- **Pipeline math: 3 trigger types × 4 horizons = 12 forecasts/run.** heat_stress excluded (rainfall model ≠ temperature model). Horizons: 3, 4 (primary/trigger-eligible), 5, 6 (advisory). Added 2026-03-15.
- **Pipeline zero records is not a failure (Mar 16).** Each source has its own cadence and lag. The incremental tracker only fetches beyond `last_ingest_date`. 0 records = nothing new since last run. Only investigate if ALL sources return 0 AND last-ingest dates are stale. Source cadence reference:
  | Source | Frequency | Typical Lag |
  |--------|-----------|-------------|
  | ERA5 | Monthly | 2–3 months |
  | Ocean Indices | Monthly | ~10 days |
  | CHIRPS | Monthly | 10–15 days |
  | NASA POWER | Daily | 1–2 days |
  | NDVI | 16-day composite | 5–10 days |
  Note: `sources_succeeded` = API connection succeeded — NOT that data was returned. All 5 can show as succeeded with 0 records ingested.
- **DB total frozen = source_ingestion_tracking is empty.** Every run logs "No tracking record found". mark_ingestion_complete() must be called explicitly after each source succeeds — it is not automatic. Added 2026-03-15.
- **Sigmoid is directionally wrong for drought probability.** Use `norm.cdf((threshold - predicted_mm) / rmse)` anchored to physical Kilombero thresholds from `rice_thresholds.RAINFALL_THRESHOLDS`. Added 2026-03-10.
- **Two config trap: CLI vs VS Code extension MCP.** Project-scoped MCP servers in `.claude.json` must match the EXACT working directory path the extension uses — parent dir ≠ subdirectory. Added 2026-03-10.
- **Pipeline Completion Timestamp Trap:** `ForecastLog.issued_at` is the write time at pipeline *completion*, not the scheduled start time. A 41-minute run starting at 03:00 UTC writes entries at 03:41 UTC — correct behavior. Never assess legitimacy from `issued_at` alone; cross-check `pipeline_executions.started_at`. Added 2026-03-19.
- **Alembic stamp required on first migration to production DB:** Production DB was created via `init_db.py` (no `alembic_version` table). Running `alembic upgrade head` fails with `DuplicateTable`. Fix: `alembic stamp <last_revision>` to register current state, then `alembic upgrade head` to apply only new migrations. Added 2026-03-30.
- **Prod-vs-Dev Compose Drift Trap:** Active stack is always `docker-compose.dev.yml`. If prod containers appear (`climate_db_prod`, `climate_frontend_prod`, `phase2-backend-N`), that is wrong — stop them and restore dev compose. Startup script `/opt/hewasense/start.sh` must always reference dev compose. Added 2026-03-19.
- **Destructive Action Gate (ALL sensitive work):** Never execute a destructive or irreversible action on user instruction alone. Required: (1) verify independently, (2) show evidence, (3) push back explicitly if data is correct. Applies to shadow run DB, server, git, model artifacts, configs. Reference case: March 19 forecast deletion — 12 valid entries deleted without verifying `issued_at` vs start time. Added 2026-03-19.

- **Scheduler 30-minute drift (Mar 15):** Scheduler was firing 30 minutes late vs scheduled time. Root cause: `misfire_grace_time` interaction with timezone offset. Fixed by explicit `timezone=self.timezone` in `CronTrigger.from_crontab()` (same root as earlier UTC/EAT fix, different symptom). Health check: `next_run_time` in scheduler status must show `:00` not `:30`.
- **System health counter KPI always zero (Mar 15):** Dashboard health metric was never incrementing. Fixed by ensuring the counter update call was placed after successful pipeline stage completion, not before.
- **Dollar sign markdown rendering bug (Mar 15):** Dashboard was rendering `$20/farmer` as broken markdown in some contexts. Fixed by escaping `$` in JSX string literals where not inside a code block.
- **Payout dedup (Mar 15):** Duplicate payout records were being created on retry. Fixed by adding idempotency check on `(farmer_id, trigger_event_id)` before insert.
- **Advisory tier enforcement (Mar 15):** Horizons 5 and 6 were incorrectly marked as trigger-eligible in the DB. Fixed by enforcing tier check at insert time in `orchestrator.py` — only horizons 3/4 get `is_insurance_trigger_eligible=True`.
- **Frontend cache inverted condition (Mar 16):** Cache hit/miss logic was inverted — serving stale data when fresh was available, re-fetching when cache was valid. Fixed by correcting boolean condition in cache check.
- **React memory leak in dashboard components (Mar 16):** Event listeners and subscriptions not cleaned up on component unmount. Fixed by returning cleanup functions from `useEffect` hooks.
- **Plotly lazy-load missing (Mar 16):** Heavy Plotly charts were imported at module load, blocking initial render. Fixed by converting to `React.lazy()` + `Suspense` wrapper.
- **GeographicMap lazy-load missing (Mar 16):** Same pattern as Plotly — large component loaded eagerly. Fixed by converting to lazy import.
- **Column cascade (Mar 16):** CSS column layout was cascading incorrectly on narrow viewports. Fixed by adding explicit breakpoint overrides.
- **Missed axios imports (Mar 16):** Several dashboard components were using `fetch()` directly instead of the project's configured axios instance (which carries auth headers). Fixed by replacing bare `fetch()` with axios calls.
- **/api/api double-prefix regression (Mar 16):** API calls were hitting `/api/api/endpoint` — double prefix. Root cause: base URL config change conflicted with existing route definitions. Fixed by stripping the duplicate prefix from the axios base URL config.
- **Sidebar AuthContext regression (Mar 16):** Sidebar was losing authentication state on route change. Root cause: AuthContext provider was mounted inside the router at a level that re-initialized on navigation. Fixed by lifting the AuthContext provider above the router.
- **TriggersDashboard hooks order crash (Mar 16):** React hooks called conditionally (`useEffect` inside an `if` block), causing "rendered more hooks than previous render" error. Fixed by moving all hook calls to unconditional top-level positions.
- **Admin health endpoint SQLAlchemy 2.x incompatibility (Mar 19):** `engine.execute()` removed in SQLAlchemy 2.x — health check endpoint was crashing with `AttributeError`. Fixed by replacing with `with engine.connect() as conn: conn.execute(text("SELECT 1"))`. Also: `audit.py` middleware was reading `request.state.user_id` (always empty — middleware runs before DI resolves user). Fixed by decoding Bearer token directly via `verify_token()` in middleware. Commit `214ecde`.
- **Admin panel Tailwind content array (Mar 21):** `tailwind.config.ts` originally listed only `LandingPage.tsx` and landing components — every other dashboard page had zero Tailwind CSS compiled (MUI handled layout so it went unnoticed). Fix: replaced specific file list with `./src/**/*.{ts,tsx}`. `preflight: false` unchanged (MUI coexistence unaffected). Commit `16077c9`.
- **Pydantic role pattern missing "manager" (Mar 21):** `UserBase.role` pattern was `^(admin|analyst|viewer)$` — seeded `manager` user failed validation on response serialization → `GET /admin/users` crashed silently → frontend showed Users (0). Fixed by adding `manager` to pattern in both `UserBase` and `UserUpdate`. Commit `16077c9`.
- **Harvard Dataverse 303→S3 trap:** `/api/access/datafile/{id}` returns 303 redirect to S3 signed URL. Use `allow_redirects=False`, extract `Location` header, then make a clean GET to S3 — do NOT carry auth/custom headers to S3 or the signature check fails (403).
- **MapSPAM 2020 unit trap:** Yield column unit is `mt/ha` (not kg/ha as older docs say). Do NOT divide by 1000. Check the `unit` column before converting.
- **Dryad download blocked by Cloudflare:** `/downloads/file_stream/{id}` serves JS challenge. `/api/v2/files/{id}/download` requires auth (401). Not automatable without browser session. Manual download required.

## Logs Index

| Date | Summary |
|------|---------|
| 2026-04-05 | Rice yield ground truth pipeline built (MapSPAM, HarvestStat, FAOSTAT/WB); Mar 15–Apr 3 session content recovered into MEMORY.md; yield calibration applied to docs — baseline 2.099 MT/Ha, loss trigger 1.259 MT/Ha |
| 2026-04-06 | Pipeline failure fixed (tz-naive/tz-aware); Farmer Value table rendering fix; timeline tone standardised across 9 docs (mid-2026 gate, No-Go branch added, TIRA/reinsurer milestones removed); TARI + IITA dataset research; Chuwa email updated to cover both Harvard Dataverse datasets |
| 2026-04-07 | ERA5 date vs datetime TypeError fixed (`c77be7a`) — hasattr guard replaced with isinstance check; chirps/nasa_power/ndvi confirmed clean; all 4 sources expected clean Apr 8; docs Phase A restructure complete (pilots/, validation/, archive/ folders); phase2/ root cleared; script path fixes after moves (`73721e2`); /log-session drift guardrail added; docs/README.md + phase2/README.md comprehensively updated (stale structure, script paths, feature count, ERA5 env var, test count); comprehensive `docs/references/` audit — stale data fixed in 7 files (hardcoded run counts removed, Jun 12→Jun 2026, heat_stress→crop_failure, 100-farmer→1,000-farmer, in-memory job store clarified, stale KILOMBERO path fixed) |

| 2026-04-09 | Investigated Apr 8 ERA5 partial failure end-to-end; confirmed Apr 7 fix deployed but exposed a downstream tz-naive/tz-aware pandas filter bug and month-boundary exclusion; patched `modules/ingestion/era5_ingestion.py`, committed `4948306`, pushed, pulled on server, restarted `pipeline-scheduler`, and verified healthy startup plus correct runtime filter behavior; created `docs/future/AUTORESEARCH_BLUEPRINT.md` with implementation roadmap, registry schema, `program.md` template, and GOTCHA-safe adoption plan |

*Last updated: 2026-04-09*
*This file is the source of truth for persistent facts. Edit directly to update.*
*Pipeline run history (daily status, forecasts, duration, sources) is in the Evidence Pack dashboard — /v1/evidence-pack/execution-log.*
