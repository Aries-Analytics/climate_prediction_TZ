# Tools Manifest — HewaSense

> Master index of all deterministic tool scripts. **Check here before writing a new script.**
> When creating a new tool, add it to this manifest with a 1-sentence description.

---

## Audit & Quality

| Tool | Path | Description |
|------|------|-------------|
| audit.py | `audit.py` | Scans codebase for forbidden patterns (reads list from `args/persona_config.yaml`). Auditor runs before every merge. |

## Forecast & ML

| Tool | Path | Description |
|------|------|-------------|
| Forecast Service | `backend/app/services/forecast_service.py` | ML model serving — generates predictions using trained ensemble (under repair, Issues 4, 7, 8). |
| Generate Forecasts | `backend/scripts/generate_forecasts.py` | Script to trigger batch forecast generation. |
| Train Pipeline | `train_pipeline.py` | Full ML training pipeline with feature engineering via preprocess.py. |
| Forecast Scheduler | `backend/app/services/forecast_scheduler.py` | Automated scheduling for periodic forecast runs. |
| Seasonal Integration | `backend/app/services/seasonal_forecast_integration.py` | Seasonal forecast model integration. |
| Backtest Script | `backend/scripts/backtest_phase_based_model.py` | Historical backtesting for phase-based parametric model. |

## Data Ingestion

| Tool | Path | Description |
|------|------|-------------|
| Load Calibrated Data | `backend/scripts/load_calibrated_data.py` | Loads calibrated 6-location climate data into database. |
| Seed Locations | `backend/seed_locations.py` | Seeds location records into database. |
| Setup Database | `backend/setup_database.py` | Database initialization and migration runner. |
| Fetch CHIRPS | `backend/scripts/fetch_recent_chirps.py` | Fetches recent CHIRPS rainfall data. |

## Memory (GOTCHA)

| Tool | Path | Description |
|------|------|-------------|
| Memory Read | `tools/memory/memory_read.py` | Loads MEMORY.md and daily logs at session start. |
| Memory Write | `tools/memory/memory_write.py` | Appends events, facts, preferences to memory store. |
| Memory DB | `tools/memory/memory_db.py` | SQLite-backed keyword search across memory entries. |
| Semantic Search | `tools/memory/semantic_search.py` | Vector similarity search for related concepts. |
| Hybrid Search | `tools/memory/hybrid_search.py` | Combined keyword + semantic search (best results). |
| Embed Memory | `tools/memory/embed_memory.py` | Generates embeddings for memory entries. |

## Monitoring & Testing

| Tool | Path | Description |
|------|------|-------------|
| Run Tests | `backend/run_tests.bat` / `.sh` | Execute full test suite with coverage. |
| Verify Setup | `backend/verify_setup.py` | Verifies database and environment setup. |
| Check Data | `backend/check_data_availability.py` | Checks data availability for locations. |

## Ground Truth (Yield Calibration)

| Tool | Path | Description |
|------|------|-------------|
| Fetch HarvestStat | `tools/ground_truth/fetch_harveststat.py` | Downloads HarvestStat Africa CSV from Dryad, filters to Tanzania rice, saves processed output. NOTE: Blocked by Cloudflare in automated context — requires manual browser download. |
| Fetch ILRI Kilombero | `tools/ground_truth/fetch_ilri_kilombero.py` | Downloads ILRI NAFAKA yield XLS from Harvard Dataverse. NOTE: File is restricted (`restricted:true`) — requires Harvard Dataverse account. |
| Fetch MapSPAM | `tools/ground_truth/fetch_mapspam.py` | Downloads MapSPAM 2020 yield ZIP (71 MB) from Harvard Dataverse S3, extracts Kilombero Basin cells, saves rainfed rice yield (rice_r, MT/Ha). |
| Fetch FAOSTAT / World Bank | `tools/ground_truth/fetch_faostat_worldbank.py` | Fetches Tanzania rice yield from FAOSTAT QCL API (when available) and World Bank AG.YLD.CREL.KG as fallback. No auth required. |
| Combine Yield Ground Truth | `tools/ground_truth/combine_yield_ground_truth.py` | Combines all ground truth sources into calibration report + JSON recommendation. Computes triangulated Kilombero baseline and loss thresholds. |

---

*When adding a new tool: create the script, test it, then add a row here.*
