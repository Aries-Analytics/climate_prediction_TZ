"""
Auto-Log Service — Stage 6 of the pipeline orchestrator.

Logs pipeline run completion metrics to the application logger.
Run history and metrics are stored in the pipeline_executions DB table
and surfaced via the Evidence Pack dashboard (/v1/evidence-pack/execution-log).

Non-blocking: any failure here is logged as a warning and does NOT affect
pipeline status or the Slack alert.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

SHADOW_RUN_TARGET_FORECASTS = 1080
SHADOW_RUN_TARGET_DAYS = 90


def run_auto_log(
    db,
    execution_id: str,
    run_date: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    sources_failed: Optional[list] = None,
) -> None:
    """
    Main entry point. Called from Stage 6 of orchestrator.execute_pipeline().

    Queries current shadow run counters from DB and emits a structured log line.
    The pipeline_executions table is the authoritative persistent record —
    no files are written and no git operations are performed.

    Args:
        db: SQLAlchemy session (read-only queries)
        execution_id: UUID of the just-completed pipeline execution
        run_date: UTC datetime of the run (defaults to now)
        duration_seconds: Pipeline duration in seconds
        sources_failed: List of failed source names ([] = all clean)
    """
    try:
        run_date = run_date or datetime.now(timezone.utc)
        sources_failed = sources_failed or []

        metrics = _query_metrics(db)
        if metrics is None:
            logger.warning("Auto-log: could not query metrics, skipping")
            return

        total_forecasts = metrics["total_forecasts"]
        valid_run_days  = metrics["valid_run_days"]
        pct = (total_forecasts / SHADOW_RUN_TARGET_FORECASTS) * 100
        eat_date = (run_date + timedelta(hours=3)).date()

        fail_str = f", sources_failed={sources_failed}" if sources_failed else ""
        logger.info(
            f"Auto-log [{eat_date}]: {total_forecasts}/{SHADOW_RUN_TARGET_FORECASTS} "
            f"({pct:.1f}%), Day {valid_run_days}, duration={duration_seconds}s"
            f"{fail_str} | execution_id={execution_id}"
        )

    except Exception as e:
        logger.warning(f"Auto-log Stage 6 failed (non-blocking): {e}", exc_info=True)


def _query_metrics(db) -> Optional[dict]:
    """Query DB for current shadow run counters."""
    try:
        from sqlalchemy import func
        from app.models.forecast_log import ForecastLog

        total = db.query(func.count(ForecastLog.id)).scalar() or 0
        valid_days = db.query(
            func.count(func.distinct(func.date(ForecastLog.issued_at)))
        ).scalar() or 0

        return {
            "total_forecasts": total,
            "valid_run_days":  valid_days,
        }
    except Exception as e:
        logger.error(f"Auto-log: metrics query failed: {e}", exc_info=True)
        return None
