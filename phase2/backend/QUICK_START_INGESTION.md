# Quick Start: Ingestion Module Integration

## What Changed?

All ingestion modules now have orchestrator-compatible functions that:
- Accept a database session
- Support date range parameters
- Return (records_fetched, records_stored) tuple

## Usage

### From Orchestrator (Automatic)

The orchestrator automatically calls the right module:

```python
from backend.app.services.pipeline.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator(db)
result = orchestrator.execute_pipeline(
    execution_type='manual',
    incremental=True
)

print(f"Status: {result.status}")
print(f"Records stored: {result.records_stored}")
```

### Direct Module Call (Manual)

```python
from datetime import datetime
from modules.ingestion.chirps_ingestion import ingest_chirps

records_fetched, records_stored = ingest_chirps(
    db=db_session,
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    incremental=False
)
```

## Testing

```bash
cd backend
python scripts/test_ingestion_integration.py
```

## See Also

- `backend/INGESTION_INTEGRATION.md` - Full integration guide
- `INGESTION_UPDATE_SUMMARY.md` - Complete change summary
