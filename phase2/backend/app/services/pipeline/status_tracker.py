"""
Pipeline Status Tracker

Provides structured access to pipeline execution status and progress
stored in PipelineExecution records.
"""
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import NamedTuple, Optional, List

from sqlalchemy.orm import Session

from app.models.pipeline_execution import PipelineExecution

logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ProgressStage(str, Enum):
    INITIALIZING = "initializing"
    INGESTING_CHIRPS = "ingesting_chirps"
    INGESTING_NASA_POWER = "ingesting_nasa_power"
    INGESTING_ERA5 = "ingesting_era5"
    INGESTING_NDVI = "ingesting_ndvi"
    INGESTING_OCEAN_INDICES = "ingesting_ocean_indices"
    INGESTING_DATA = "ingesting_data"
    GENERATING_FORECASTS = "generating_forecasts"
    CREATING_RECOMMENDATIONS = "creating_recommendations"
    FINALIZING = "finalizing"


class ExecutionStatus(NamedTuple):
    execution_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    records_stored: int
    forecasts_generated: int
    error_message: Optional[str]
    sources_failed: List[str]
    sources_succeeded: List[str]


class ProgressInfo(NamedTuple):
    execution_id: str
    current_stage: str
    progress_percentage: int
    completed_sources: int
    total_sources: int
    updated_at: Optional[datetime]


class StatusTracker:
    """
    Reads and writes pipeline execution status from the database.

    Uses PipelineExecution rows as the source of truth — no in-memory
    state is kept between calls.
    """

    def __init__(self, db: Session):
        self._db = db
        # In-memory progress store for within-execution tracking
        self._progress: dict[str, dict] = {}

    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """
        Retrieve the status of a specific pipeline execution.

        Args:
            execution_id: UUID string of the pipeline execution.

        Returns:
            ExecutionStatus named tuple, or None if not found.
        """
        execution = (
            self._db.query(PipelineExecution)
            .filter(PipelineExecution.id == execution_id)
            .first()
        )
        if execution is None:
            logger.warning(f"No execution found for id={execution_id}")
            return None

        return ExecutionStatus(
            execution_id=execution.id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_seconds=execution.duration_seconds,
            records_stored=execution.records_stored or 0,
            forecasts_generated=execution.forecasts_generated or 0,
            error_message=execution.error_message,
            sources_failed=execution.sources_failed or [],
            sources_succeeded=execution.sources_succeeded or [],
        )

    def update_progress(
        self,
        execution_id: str,
        stage: str,
        progress_percentage: int,
        completed_sources: int,
        total_sources: int,
    ) -> None:
        """
        Record current progress for a running pipeline execution.

        Progress is stored in-memory and returned by get_progress().
        The progress_percentage is clamped to [0, 100].

        Args:
            execution_id: UUID of the running execution.
            stage: Current pipeline stage name.
            progress_percentage: Completion percentage 0-100.
            completed_sources: Number of data sources finished.
            total_sources: Total data sources to process.
        """
        clamped_pct = max(0, min(100, progress_percentage))
        self._progress[execution_id] = {
            "current_stage": stage,
            "progress_percentage": clamped_pct,
            "completed_sources": completed_sources,
            "total_sources": total_sources,
            "updated_at": datetime.now(timezone.utc),
        }
        logger.debug(
            f"Progress update [{execution_id}]: stage={stage} "
            f"{clamped_pct}% ({completed_sources}/{total_sources})"
        )

    def get_progress(self, execution_id: str) -> Optional[ProgressInfo]:
        """
        Retrieve progress for a running pipeline execution.

        Args:
            execution_id: UUID of the running execution.

        Returns:
            ProgressInfo named tuple, or None if no progress recorded.
        """
        data = self._progress.get(execution_id)
        if data is None:
            logger.warning(f"No progress recorded for execution_id={execution_id}")
            return None

        return ProgressInfo(
            execution_id=execution_id,
            current_stage=data["current_stage"],
            progress_percentage=data["progress_percentage"],
            completed_sources=data["completed_sources"],
            total_sources=data["total_sources"],
            updated_at=data["updated_at"],
        )
