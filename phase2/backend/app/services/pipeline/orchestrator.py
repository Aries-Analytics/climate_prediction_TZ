"""
Pipeline Orchestrator

Coordinates pipeline stages, manages execution locking, and handles retries.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, NamedTuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.pipeline_execution import PipelineExecution, DataQualityMetrics
from app.models.forecast_log import ForecastLog
from app.services.pipeline.incremental_manager import IncrementalIngestionManager
from app.services.pipeline.retry_handler import RetryHandler
from app.services.pipeline.data_quality import DataQualityValidator
from app.services.pipeline.alert_service import AlertService

logger = logging.getLogger(__name__)


class ExecutionResult(NamedTuple):
    """Result of pipeline execution"""
    execution_id: str
    status: str  # 'completed' | 'failed' | 'partial'
    records_fetched: int
    records_stored: int
    forecasts_generated: int
    recommendations_created: int
    sources_succeeded: list
    sources_failed: list
    per_source_records: dict = {}  # {source_name: records_stored}
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None


class IngestionResult(NamedTuple):
    """Result of data ingestion stage"""
    records_fetched: int
    records_stored: int
    sources_succeeded: list
    sources_failed: list
    per_source_records: dict = {}  # {source_name: records_stored}
    error_message: Optional[str] = None


class ForecastResult(NamedTuple):
    """Result of forecast generation stage"""
    forecasts_generated: int
    recommendations_created: int
    error_message: Optional[str] = None


class ExecutionStatus(NamedTuple):
    """Current status of pipeline execution"""
    execution_id: str
    status: str
    started_at: datetime
    current_stage: Optional[str] = None
    progress_pct: Optional[float] = None


class PipelineOrchestrator:
    """
    Orchestrates pipeline execution with locking and stage coordination.
    
    Coordinates:
    - Execution locking to prevent concurrent runs
    - Ingestion → Validation → Forecasting stages
    - Error handling and retry logic
    - Progress tracking and metadata recording
    """
    
    LOCK_ID = 123456  # Advisory lock ID for pipeline execution
    
    def __init__(self, db: Session, alert_service: Optional[AlertService] = None):
        """
        Initialize the pipeline orchestrator
        
        Args:
            db: Database session
            alert_service: Optional alert service for notifications
        """
        self.db = db
        self.incremental_manager = IncrementalIngestionManager(db)
        self.data_quality_validator = DataQualityValidator()
        self.alert_service = alert_service
        
        # Retry handler for data source API calls (3 attempts, exponential backoff)
        self.data_retry_handler = RetryHandler(
            max_attempts=3,
            initial_delay=2.0,
            backoff_factor=2.0,
            max_delay=60.0
        )
        # Retry handler for forecast generation (1 retry after 5 minutes)
        self.forecast_retry_handler = RetryHandler(
            max_attempts=2,  # 1 initial + 1 retry
            initial_delay=300.0,  # 5 minutes
            backoff_factor=1.0,  # No exponential increase
            max_delay=300.0
        )
    
    def acquire_lock(self) -> bool:
        """
        Acquire execution lock to prevent concurrent runs.

        Uses a DEDICATED raw DB connection (NullPool) for the advisory lock,
        separate from the ORM session. NullPool ensures connection.close()
        truly terminates the PostgreSQL backend — preventing stale session-level
        advisory locks from persisting across runs due to connection pooling.

        Returns:
            True if lock acquired, False if already locked
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            from app.core.config import settings

            # NullPool: every close() truly closes the underlying Postgres connection,
            # guaranteeing the session-level advisory lock is released.
            self._lock_engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
            self._lock_connection = self._lock_engine.connect()

            result = self._lock_connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": self.LOCK_ID}
            ).scalar()

            if result:
                logger.info(f"Acquired pipeline execution lock (ID: {self.LOCK_ID})")
                return True
            else:
                logger.warning(f"Pipeline execution lock already held (ID: {self.LOCK_ID})")
                self._lock_connection.close()
                self._lock_connection = None
                self._lock_engine.dispose()
                self._lock_engine = None
                return False
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            if hasattr(self, '_lock_connection') and self._lock_connection:
                self._lock_connection.close()
                self._lock_connection = None
            if hasattr(self, '_lock_engine') and self._lock_engine:
                self._lock_engine.dispose()
                self._lock_engine = None
            return False

    def release_lock(self) -> None:
        """Release execution lock by explicitly unlocking then closing the connection.

        Calls pg_advisory_unlock explicitly before close() as a belt-and-suspenders
        measure, then disposes the NullPool engine to guarantee the underlying
        PostgreSQL session terminates and the advisory lock is freed.
        """
        try:
            if hasattr(self, '_lock_connection') and self._lock_connection:
                try:
                    self._lock_connection.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": self.LOCK_ID}
                    )
                except Exception:
                    pass  # Best-effort; engine.dispose() will close the connection regardless
                self._lock_connection.close()
                self._lock_connection = None
                logger.info(f"Released pipeline execution lock (ID: {self.LOCK_ID})")
            else:
                logger.warning("No lock connection to release")
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            self._lock_connection = None
        finally:
            # Always dispose the engine — with NullPool this terminates the Postgres backend
            if hasattr(self, '_lock_engine') and self._lock_engine:
                try:
                    self._lock_engine.dispose()
                except Exception:
                    pass
                self._lock_engine = None
    
    def execute_pipeline(
        self, 
        execution_type: str = 'scheduled',
        incremental: bool = True
    ) -> ExecutionResult:
        """
        Execute full pipeline: ingestion → validation → forecasting
        
        Args:
            execution_type: 'scheduled' or 'manual'
            incremental: Whether to use incremental ingestion
            
        Returns:
            ExecutionResult with summary of execution
        """
        execution_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        
        # Try to acquire lock
        if not self.acquire_lock():
            return ExecutionResult(
                execution_id=execution_id,
                status='failed',
                records_fetched=0,
                records_stored=0,
                forecasts_generated=0,
                recommendations_created=0,
                sources_succeeded=[],
                sources_failed=[],
                error_message="Pipeline is already running (concurrent execution prevented)"
            )
        
        try:
            # Create execution record
            execution = PipelineExecution(
                id=execution_id,
                execution_type=execution_type,
                status='running',
                started_at=started_at
            )
            self.db.add(execution)
            self.db.commit()
            
            logger.info(f"Starting pipeline execution {execution_id} ({execution_type})")
            
            # Stage 1: Data Ingestion
            logger.info("Stage 1: Data Ingestion")
            ingestion_result = self.execute_ingestion(incremental=incremental)
            
            # Update execution with ingestion results
            execution.records_fetched = ingestion_result.records_fetched
            execution.records_stored = ingestion_result.records_stored
            execution.sources_succeeded = ingestion_result.sources_succeeded
            execution.sources_failed = ingestion_result.sources_failed
            self.db.commit()
            
            # Check if ingestion completely failed
            if not ingestion_result.sources_succeeded:
                raise Exception(f"All data sources failed: {ingestion_result.error_message}")
            
            # Stage 2: Forecast Generation
            logger.info("Stage 2: Forecast Generation")
            
            # Pass information about partial data to forecast generation
            has_partial_data = len(ingestion_result.sources_failed) > 0
            forecast_result = self.execute_forecasting(partial_data=has_partial_data)
            
            # Update execution with forecast results
            execution.forecasts_generated = forecast_result.forecasts_generated
            execution.recommendations_created = forecast_result.recommendations_created
            self.db.commit()

            # Stage 3: Evaluate matured forecasts
            # Resolve any ForecastLog entries whose valid_until date has passed
            logger.info("Stage 3: Evaluating matured forecasts")
            try:
                from app.services.evaluation_service import ForecastEvaluator
                eval_result = ForecastEvaluator(self.db).evaluate_pending_forecasts()
                evaluated = eval_result.get("processed", 0)
                if evaluated:
                    logger.info(f"Resolved {evaluated} matured ForecastLog entries")
            except Exception as eval_err:
                # Non-fatal — log and continue; forecasts stay pending until next run
                logger.warning(f"Forecast evaluation stage failed (non-fatal): {eval_err}")

            # Determine final status
            if ingestion_result.sources_failed:
                final_status = 'partial'  # Some sources failed
                error_msg = f"Partial failure: {len(ingestion_result.sources_failed)} sources failed"
            else:
                final_status = 'completed'
                error_msg = None
            
            # Complete execution
            completed_at = datetime.now(timezone.utc)
            duration = int((completed_at - started_at).total_seconds())
            
            execution.status = final_status
            execution.completed_at = completed_at
            execution.duration_seconds = duration
            execution.error_message = error_msg
            self.db.commit()
            
            logger.info(
                f"Pipeline execution {execution_id} {final_status}: "
                f"{ingestion_result.records_stored} records, "
                f"{forecast_result.forecasts_generated} forecasts in {duration}s"
            )
            
            return ExecutionResult(
                execution_id=execution_id,
                status=final_status,
                records_fetched=ingestion_result.records_fetched,
                records_stored=ingestion_result.records_stored,
                forecasts_generated=forecast_result.forecasts_generated,
                recommendations_created=forecast_result.recommendations_created,
                sources_succeeded=ingestion_result.sources_succeeded,
                sources_failed=ingestion_result.sources_failed,
                per_source_records=ingestion_result.per_source_records,
                error_message=error_msg,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Pipeline execution {execution_id} failed: {e}", exc_info=True)
            
            # Update execution record with failure
            execution.status = 'failed'
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = int((execution.completed_at - started_at).total_seconds())
            execution.error_message = str(e)
            execution.error_traceback = self._get_traceback()
            self.db.commit()
            
            return ExecutionResult(
                execution_id=execution_id,
                status='failed',
                records_fetched=execution.records_fetched or 0,
                records_stored=execution.records_stored or 0,
                forecasts_generated=execution.forecasts_generated or 0,
                recommendations_created=execution.recommendations_created or 0,
                sources_succeeded=execution.sources_succeeded or [],
                sources_failed=execution.sources_failed or [],
                error_message=str(e),
                duration_seconds=execution.duration_seconds
            )
        finally:
            # Always release lock
            self.release_lock()
    
    def execute_ingestion(self, incremental: bool = True) -> IngestionResult:
        """
        Execute data ingestion with incremental update logic and graceful degradation
        
        Implements graceful degradation: if one data source fails, continue with others.
        Uses retry logic for each source (3 attempts with exponential backoff).
        
        Args:
            incremental: Whether to use incremental fetching
            
        Returns:
            IngestionResult with summary
        """
        logger.info("Executing data ingestion (incremental={})".format(incremental))
        
        # Data sources to ingest
        sources = ['chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices']
        
        total_records_fetched = 0
        total_records_stored = 0
        sources_succeeded = []
        sources_failed = []
        per_source_records = {}  # Track per-source record counts
        errors = []
        
        # Process each source independently (graceful degradation)
        for source in sources:
            try:
                logger.info(f"Ingesting data from source: {source}")
                
                # Use retry handler for API calls
                def _ingest_source():
                    return self._ingest_single_source(source, incremental)
                
                result = self.data_retry_handler.retry(_ingest_source)
                
                if result is None:
                    # All retries exhausted
                    logger.error(f"Source {source} failed after all retries")
                    sources_failed.append(source)
                    errors.append(f"{source}: All retries exhausted")
                else:
                    # Success
                    records_fetched, records_stored = result
                    total_records_fetched += records_fetched
                    total_records_stored += records_stored
                    per_source_records[source] = records_stored
                    sources_succeeded.append(source)
                    logger.info(f"Source {source} succeeded: {records_stored} records stored")
                    
            except Exception as e:
                # Catch any unexpected errors
                logger.error(f"Unexpected error ingesting {source}: {e}", exc_info=True)
                sources_failed.append(source)
                errors.append(f"{source}: {str(e)}")
        
        # Determine error message
        error_message = None
        if sources_failed:
            error_message = f"Failed sources: {', '.join(errors)}"
        
        return IngestionResult(
            records_fetched=total_records_fetched,
            records_stored=total_records_stored,
            sources_succeeded=sources_succeeded,
            sources_failed=sources_failed,
            per_source_records=per_source_records,
            error_message=error_message
        )
    
    def _ingest_single_source(self, source: str, incremental: bool) -> tuple:
        """
        Ingest data from a single source
        
        Args:
            source: Source name
            incremental: Whether to use incremental fetching
            
        Returns:
            Tuple of (records_fetched, records_stored)
        """
        from datetime import datetime, timedelta
        
        logger.info(f"Ingesting from {source} (incremental={incremental})")
        
        # Determine date range based on incremental flag
        if incremental:
            # Get last ingestion date for this source using correct method
            date_range = self.incremental_manager.calculate_fetch_range(source)
            start_date = date_range.start_date
            end_date = date_range.end_date
        else:
            # Full refresh - fetch all available data
            start_date = datetime(2010, 1, 1)
            end_date = datetime.now(timezone.utc)
        
        logger.info(f"Date range for {source}: {start_date} to {end_date}")
        
        # Call appropriate ingestion module
        try:
            if source == 'chirps':
                from modules.ingestion.chirps_ingestion import ingest_chirps
                return ingest_chirps(self.db, start_date, end_date, incremental)
            
            elif source == 'nasa_power':
                from modules.ingestion.nasa_power_ingestion import ingest_nasa_power
                return ingest_nasa_power(self.db, start_date, end_date, incremental)
            
            elif source == 'era5':
                from modules.ingestion.era5_ingestion import ingest_era5
                return ingest_era5(self.db, start_date, end_date, incremental)
            
            elif source == 'ndvi':
                from modules.ingestion.ndvi_ingestion import ingest_ndvi
                return ingest_ndvi(self.db, start_date, end_date, incremental)
            
            elif source == 'ocean_indices':
                from modules.ingestion.ocean_indices_ingestion import ingest_ocean_indices
                return ingest_ocean_indices(self.db, start_date, end_date, incremental)
            
            else:
                logger.warning(f"Unknown source: {source}")
                return (0, 0)
                
        except Exception as e:
            logger.error(f"Failed to ingest from {source}: {e}", exc_info=True)
            raise
    
    def execute_forecasting(self, partial_data: bool = False) -> ForecastResult:
        """
        Execute forecast generation and recommendations with retry logic
        
        Retries once after 5 minutes if forecast generation fails.
        Handles partial data scenarios by flagging reduced confidence.
        
        Args:
            partial_data: Whether some data sources failed (reduced confidence)
        
        Returns:
            ForecastResult with summary
        """
        if partial_data:
            logger.warning("Generating forecasts with partial data - reduced confidence expected")
        else:
            logger.info("Executing forecast generation")
        
        def _generate_forecasts():
            """Inner function for retry logic"""
            from app.services.forecast_service import generate_forecasts, generate_all_recommendations
            from app.config.rice_thresholds import get_horizon_tier

            # Calibrated probability thresholds (warning-level per hazard type).
            # Source: THRESHOLD_ANALYSIS_INDUSTRY_RESEARCH.md + KILOMBERO_BASIN_PILOT_SPECIFICATION.md
            _PROB_THRESHOLDS = {
                "drought":      0.65,
                "flood":        0.65,
                "heat_stress":  0.60,
                "crop_failure": 0.60,
            }

            # Generate forecasts (with available data)
            forecasts = generate_forecasts(self.db)

            # If partial data, flag forecasts with reduced confidence
            if partial_data:
                for forecast in forecasts:
                    logger.info(f"Forecast {forecast.id} generated with partial data")

            # Formally log this execution in the shadow-run ForecastLog
            import uuid
            log_batch = []
            for f in forecasts:
                tier = get_horizon_tier(f.horizon_months)
                fl = ForecastLog(
                    id=str(uuid.uuid4()),
                    issued_at=datetime.now(timezone.utc),
                    valid_from=f.forecast_date,
                    valid_until=f.target_date,
                    region_id=str(f.location_id),
                    model_version=f.model_version or "V4.0",
                    forecast_type=f.trigger_type,
                    forecast_value=f.probability,
                    lead_time_days=f.horizon_months * 30,
                    status="pending",
                    threshold_used=_PROB_THRESHOLDS.get(f.trigger_type),
                    forecast_distribution={
                        "horizon_tier": tier,
                        "is_insurance_trigger_eligible": tier == "primary",
                        "confidence_lower": float(f.confidence_lower),
                        "confidence_upper": float(f.confidence_upper),
                    }
                )
                log_batch.append(fl)
            
            if log_batch:
                self.db.bulk_save_objects(log_batch)
                self.db.commit()
                logger.info(f"Saved {len(log_batch)} ForecastLog evidence snapshots for Shadow-Run")
            
            # Generate recommendations
            recommendations = generate_all_recommendations(self.db, min_probability=0.3)
            
            return forecasts, recommendations
        
        try:
            # Execute with retry logic (1 retry after 5 minutes)
            result = self.forecast_retry_handler.retry(_generate_forecasts)
            
            if result is None:
                # All retries exhausted
                return ForecastResult(
                    forecasts_generated=0,
                    recommendations_created=0,
                    error_message="Forecast generation failed after retry"
                )
            
            forecasts, recommendations = result
            
            error_msg = None
            if partial_data:
                error_msg = "Forecasts generated with partial data (reduced confidence)"
            
            return ForecastResult(
                forecasts_generated=len(forecasts),
                recommendations_created=len(recommendations),
                error_message=error_msg
            )
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}", exc_info=True)
            return ForecastResult(
                forecasts_generated=0,
                recommendations_created=0,
                error_message=str(e)
            )
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """
        Get current status of pipeline execution
        
        Args:
            execution_id: Execution ID to query
            
        Returns:
            ExecutionStatus or None if not found
        """
        execution = self.db.query(PipelineExecution).filter(
            PipelineExecution.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        # Determine current stage based on status and metrics
        current_stage = None
        progress_pct = None
        
        if execution.status == 'running':
            if execution.forecasts_generated > 0:
                current_stage = 'forecasting'
                progress_pct = 75.0
            elif execution.records_stored > 0:
                current_stage = 'ingestion'
                progress_pct = 50.0
            else:
                current_stage = 'starting'
                progress_pct = 10.0
        elif execution.status in ['completed', 'partial']:
            current_stage = 'completed'
            progress_pct = 100.0
        elif execution.status == 'failed':
            current_stage = 'failed'
            progress_pct = 0.0
        
        return ExecutionStatus(
            execution_id=execution.id,
            status=execution.status,
            started_at=execution.started_at,
            current_stage=current_stage,
            progress_pct=progress_pct
        )
    
    def validate_data_quality(
        self,
        source: str,
        data_df,
        execution_id: str
    ) -> None:
        """
        Validate data quality and store metrics
        
        Args:
            source: Data source name
            data_df: DataFrame with ingested data
            execution_id: Pipeline execution ID
        """
        try:
            import pandas as pd
            
            # Convert to DataFrame if needed
            if not isinstance(data_df, pd.DataFrame):
                logger.warning(f"Data for {source} is not a DataFrame, skipping validation")
                return
            
            # Validate data quality
            validation_result = self.data_quality_validator.validate_climate_data(data_df)
            
            # Store quality metrics
            quality_metrics = DataQualityMetrics(
                execution_id=execution_id,
                source=source,
                total_records=validation_result.total_records,
                missing_values_count=len(validation_result.missing_fields),
                out_of_range_count=len(validation_result.anomalies),
                data_gaps_count=len(validation_result.data_gaps),
                quality_score=validation_result.quality_score,
                anomalies=[
                    {
                        'field': a.field,
                        'value': a.value,
                        'expected_range': a.expected_range,
                        'date': str(a.date) if a.date else None
                    }
                    for a in validation_result.anomalies[:10]  # Limit to first 10
                ]
            )
            self.db.add(quality_metrics)
            self.db.commit()
            
            logger.info(
                f"Data quality for {source}: score={validation_result.quality_score:.2f}, "
                f"anomalies={len(validation_result.anomalies)}, "
                f"gaps={len(validation_result.data_gaps)}"
            )
            
            # Send alert if quality check fails
            if not validation_result.is_valid and self.alert_service:
                issues = []
                if validation_result.missing_fields:
                    issues.append(f"Missing fields: {', '.join(validation_result.missing_fields)}")
                if validation_result.anomalies:
                    issues.append(f"{len(validation_result.anomalies)} anomalies detected")
                if validation_result.data_gaps:
                    issues.append(f"{len(validation_result.data_gaps)} data gaps found")
                
                self.alert_service.send_quality_failure_alert(
                    source=source,
                    issues=issues,
                    execution_id=execution_id
                )
            
        except Exception as e:
            logger.error(f"Failed to validate data quality for {source}: {e}", exc_info=True)
    
    def _get_traceback(self) -> str:
        """Get current exception traceback as string"""
        import traceback
        return traceback.format_exc()
