# Ingestion Module Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AUTOMATED PIPELINE                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Pipeline Orchestrator                          │    │
│  │                                                             │    │
│  │  • Execution locking (PostgreSQL advisory locks)           │    │
│  │  • Retry logic (3 attempts, exponential backoff)           │    │
│  │  • Graceful degradation (continue on partial failure)      │    │
│  │  • Progress tracking & metadata recording                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │         _ingest_single_source(source, incremental)         │    │
│  │                                                             │    │
│  │  1. Determine date range (incremental or full)             │    │
│  │  2. Route to appropriate ingestion module                  │    │
│  │  3. Return (records_fetched, records_stored)               │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐     ┌───────────────┐
│    CHIRPS     │      │  NASA POWER   │     │     ERA5      │
│               │      │               │     │               │
│ Rainfall data │      │ Temperature   │     │ Reanalysis    │
│ from GEE      │      │ from API      │     │ from CDS      │
└───────┬───────┘      └───────┬───────┘     └───────┬───────┘
        │                      │                      │
        │              ┌───────┴───────┐              │
        │              │               │              │
        ▼              ▼               ▼              ▼
┌───────────────┐      ┌───────────────┐     ┌───────────────┐
│     NDVI      │      │ Ocean Indices │     │               │
│               │      │               │     │               │
│ Vegetation    │      │ ENSO & IOD    │     │               │
│ from MODIS    │      │ from NOAA     │     │               │
└───────┬───────┘      └───────┬───────┘     └───────────────┘
        │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ClimateData DB    │
                    │                     │
                    │  • date             │
                    │  • location_lat     │
                    │  • location_lon     │
                    │  • temperature_avg  │
                    │  • rainfall_mm      │
                    │  • ndvi             │
                    │  • enso_index       │
                    │  • iod_index        │
                    └─────────────────────┘
```

## Data Flow

### 1. Orchestrator Initiates Ingestion

```
orchestrator.execute_pipeline()
    │
    ├─ acquire_lock()
    ├─ create_execution_record()
    │
    └─ execute_ingestion(incremental=True)
           │
           └─ For each source: ['chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices']
                  │
                  └─ data_retry_handler.retry(_ingest_source)
                         │
                         └─ _ingest_single_source(source, incremental)
```

### 2. Single Source Ingestion

```
_ingest_single_source('chirps', incremental=True)
    │
    ├─ Determine date range
    │     │
    │     ├─ If incremental: get_date_range(source)
    │     │     └─ Returns: (last_ingestion_date, now)
    │     │
    │     └─ If full: (2010-01-01, now)
    │
    ├─ Import module
    │     └─ from modules.ingestion.chirps_ingestion import ingest_chirps
    │
    └─ Call ingestion function
          └─ ingest_chirps(db, start_date, end_date, incremental)
                 │
                 └─ Returns: (records_fetched, records_stored)
```

### 3. Module Execution

```
ingest_chirps(db, start_date, end_date, incremental)
    │
    ├─ Fetch data
    │     └─ fetch_chirps_data(start_year, end_year)
    │           │
    │           ├─ Try: Google Earth Engine (real data)
    │           ├─ Fallback: Cached data
    │           └─ Last resort: Synthetic data
    │
    ├─ Filter to date range
    │     └─ df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    │
    ├─ Store to database (upsert)
    │     │
    │     └─ For each record:
    │           ├─ Check if exists (by date + location)
    │           ├─ Update if exists
    │           └─ Insert if new
    │
    ├─ Commit transaction
    │
    └─ Return (records_fetched, records_stored)
```

## Module Interface

All modules implement this interface:

```python
def ingest_<source>(
    db: Session,                          # Database session
    start_date: Optional[datetime],       # Start of date range
    end_date: Optional[datetime],         # End of date range
    incremental: bool                     # Incremental or full refresh
) -> Tuple[int, int]:                     # (fetched, stored)
```

## Error Handling Flow

```
orchestrator.execute_ingestion()
    │
    └─ For each source:
           │
           ├─ Try: _ingest_single_source()
           │     │
           │     ├─ Attempt 1 ──┐
           │     ├─ Attempt 2 ──┼─ data_retry_handler (3 attempts)
           │     └─ Attempt 3 ──┘
           │           │
           │           ├─ Success → sources_succeeded.append(source)
           │           └─ Failure → sources_failed.append(source)
           │
           └─ Continue to next source (graceful degradation)
```

## Database Upsert Pattern

```
For each data record:
    │
    ├─ Query existing record
    │     WHERE date = record.date
    │     AND location_lat = record.lat
    │     AND location_lon = record.lon
    │
    ├─ If exists:
    │     └─ UPDATE fields (e.g., rainfall_mm, temperature_avg)
    │
    └─ If not exists:
          └─ INSERT new ClimateData record
```

## Execution Result

```
ExecutionResult
├─ execution_id: str
├─ status: 'completed' | 'partial' | 'failed'
├─ records_fetched: int
├─ records_stored: int
├─ forecasts_generated: int
├─ recommendations_created: int
├─ sources_succeeded: ['chirps', 'nasa_power', ...]
├─ sources_failed: ['era5', ...]
├─ error_message: Optional[str]
└─ duration_seconds: int
```
