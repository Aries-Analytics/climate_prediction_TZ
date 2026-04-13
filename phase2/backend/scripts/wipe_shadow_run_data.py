"""
Shadow Run v2 — Clean Slate DB Wipe Script

Wipes pipeline/forecast tables to prepare for the two-zone Kilombero Basin
shadow run restart (Ifakara TC + Mlimba DC).

GOTCHA Compliance:
  - Law #1 (NO SYNTHETIC FALLBACKS): Script raises on failure, never silently skips.
  - Law #5 (DATA TRUTH): All timestamps are UTC-aware.
  - Law #6 (FEATURE ALIGNMENT): Does NOT touch feature_schema.json or active_model.json.
  - Law #8 (AUTONOMOUS DOCUMENTATION): Caller must update docs after successful wipe.

Tables WIPED:
  - forecast_logs          (old shadow run forecasts from wrong coordinates)
  - pipeline_executions    (execution history from old runs)
  - ndvi_observations      (NDVI correlation data tied to old shadow run)
  - data_quality_metrics   (FK-cascades from pipeline_executions)
  - source_ingestion_tracking (will be repopulated on first new run)

Tables PRESERVED:
  - climate_data           (historical training data 2000-2025, feeds ML model)
  - locations              (all 8: 6 training + 2 new pilot zones)
  - forecasts              (latest forecast snapshot, will be overwritten on first run)
  - All other tables       (users, simulations, triggers, etc.)

Usage:
  cd /root/workspace/hewasense/phase2/backend
  python scripts/wipe_shadow_run_data.py [--confirm]

  Without --confirm, runs in dry-run mode (counts only, no deletions).
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.forecast_log import ForecastLog
from app.models.pipeline_execution import PipelineExecution, DataQualityMetrics, SourceIngestionTracking
from app.models.ndvi_observation import NdviObservation


# Tables to wipe, in FK-safe order (children before parents)
WIPE_TARGETS = [
    ("data_quality_metrics", DataQualityMetrics),
    ("source_ingestion_tracking", SourceIngestionTracking),
    ("ndvi_observations", NdviObservation),
    ("forecast_logs", ForecastLog),
    ("pipeline_executions", PipelineExecution),
]

# Tables explicitly preserved (documented for audit trail)
PRESERVED_TABLES = [
    "climate_data",
    "locations",
    "forecasts",
    "forecast_recommendations",
    "forecast_validations",
    "trigger_events",
    "users",
]


def wipe_shadow_run_data(db: Session, dry_run: bool = True) -> dict:
    """
    Wipe shadow run tables for clean slate restart.

    Args:
        db: SQLAlchemy session
        dry_run: If True, only count rows without deleting

    Returns:
        Dict with per-table row counts (before deletion)

    Raises:
        RuntimeError: If any table wipe fails (Law #1: no silent failures)
    """
    now = datetime.now(timezone.utc)  # Law #5: UTC-aware
    results = {}

    print("=" * 60)
    print(f"Shadow Run v2 — Clean Slate DB Wipe")
    print(f"Timestamp: {now.isoformat()}")
    print(f"Mode: {'DRY RUN (no deletions)' if dry_run else 'LIVE — DELETING DATA'}")
    print("=" * 60)

    for table_name, model_class in WIPE_TARGETS:
        try:
            count = db.query(model_class).count()
            results[table_name] = count
            print(f"\n  {table_name}: {count} rows", end="")

            if not dry_run and count > 0:
                db.query(model_class).delete()
                print(f" -> DELETED", end="")
            elif not dry_run and count == 0:
                print(f" -> (empty, skipped)", end="")

        except Exception as e:
            # Law #1: No silent failures — raise explicitly
            raise RuntimeError(
                f"Failed to wipe table '{table_name}': {e}. "
                f"DB state may be inconsistent — check manually."
            ) from e

    if not dry_run:
        db.commit()
        print(f"\n\n  COMMITTED. All tables wiped successfully.")
    else:
        print(f"\n\n  Dry run complete. No data was deleted.")
        print(f"  Re-run with --confirm to execute the wipe.")

    print(f"\n  Preserved tables (untouched):")
    for t in PRESERVED_TABLES:
        print(f"    - {t}")

    print("\n" + "=" * 60)
    print("Law #8 reminder: Update memory/logs/ and MEMORY.md after wipe.")
    print("=" * 60)

    return results


def main():
    """Main entry point."""
    dry_run = "--confirm" not in sys.argv

    if not dry_run:
        print("\n  WARNING: This will permanently delete shadow run data.")
        print("  Tables: forecast_logs, pipeline_executions, ndvi_observations,")
        print("          data_quality_metrics, source_ingestion_tracking")
        print("  Preserved: climate_data, locations, forecasts, users\n")
        response = input("  Type 'WIPE' to confirm: ")
        if response.strip() != "WIPE":
            print("  Aborted.")
            sys.exit(0)

    db = SessionLocal()
    try:
        results = wipe_shadow_run_data(db, dry_run=dry_run)
        total = sum(results.values())
        action = "would be deleted" if dry_run else "deleted"
        print(f"\n  Total: {total} rows {action} across {len(results)} tables.")
    except RuntimeError as e:
        print(f"\n  FATAL: {e}")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n  UNEXPECTED ERROR: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
