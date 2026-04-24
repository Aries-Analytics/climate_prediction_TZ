"""
Pipeline Scheduler Service

Schedules automated pipeline execution using APScheduler.
"""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.services.pipeline.orchestrator import PipelineOrchestrator, ExecutionResult
from app.services.pipeline.alert_service import AlertService

logger = logging.getLogger(__name__)


def execute_pipeline_standalone(alert_service_config: Optional[dict] = None) -> None:
    """
    Standalone function to execute pipeline (called by APScheduler)
    
    This function is separate from the class to avoid serialization issues.
    
    Args:
        alert_service_config: Optional alert service configuration
    """
    logger.info("Scheduled pipeline execution starting")
    
    try:
        # Create database session
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Recreate alert service if config provided
            alert_service = None
            if alert_service_config:
                alert_service = AlertService(
                    email_enabled=alert_service_config.get('email_enabled', False),
                    slack_enabled=alert_service_config.get('slack_enabled', False),
                    slack_webhook_url=alert_service_config.get('slack_webhook_url')
                )
            
            orchestrator = PipelineOrchestrator(db, alert_service)
            result = orchestrator.execute_pipeline(execution_type='scheduled')
            
            logger.info(
                f"Scheduled execution completed: {result.status}, "
                f"execution_id={result.execution_id}, "
                f"duration={result.duration_seconds}s"
            )
            
            # Compute dynamic next run time from schedule config
            next_run_str = None
            try:
                import os
                import pytz
                schedule = os.environ.get('PIPELINE_SCHEDULE', '0 6 * * *')
                tz_name = os.environ.get('PIPELINE_TIMEZONE', 'Africa/Dar_es_Salaam')
                tz = pytz.timezone(tz_name)
                from apscheduler.triggers.cron import CronTrigger
                trigger = CronTrigger.from_crontab(schedule, timezone=tz)
                next_fire = trigger.get_next_fire_time(None, datetime.now(tz))
                if next_fire:
                    next_run_str = next_fire.strftime('%A, %b %d at %H:%M %Z')
            except Exception as e:
                logger.warning(f"Could not compute next run time: {e}")
            
            # Send alerts based on execution status
            if alert_service:
                if result.status == 'failed':
                    # Don't send CRITICAL for lock contention — it's expected behavior
                    # when a run is still in progress from a previous trigger
                    if 'already running' in (result.error_message or ''):
                        logger.info(
                            f"Skipped execution (pipeline already running). "
                            f"This is normal when a run overlaps with the next trigger."
                        )
                    else:
                        # Determine which stage failed
                        failed_stage = "Pipeline"
                        if result.sources_succeeded or result.sources_failed:
                            if result.forecasts_generated == 0 and result.records_stored > 0:
                                failed_stage = "Forecast Generation"
                            elif result.records_stored == 0:
                                failed_stage = "Data Ingestion"
                        
                        alert_service.send_pipeline_failure_rich_alert(
                            execution_id=result.execution_id,
                            error_message=result.error_message or "Pipeline execution failed",
                            duration_seconds=result.duration_seconds,
                            sources_succeeded=result.sources_succeeded,
                            sources_failed=result.sources_failed,
                            failed_stage=failed_stage,
                            forecasts_generated=result.forecasts_generated,
                        )
                elif result.status == 'partial':
                    alert_service.send_partial_failure_alert(
                        failed_sources=result.sources_failed,
                        succeeded_sources=result.sources_succeeded,
                        execution_id=result.execution_id
                    )
                elif result.status == 'completed':
                    # Send rich success alert with full context
                    alert_service.send_pipeline_success_alert(
                        execution_id=result.execution_id,
                        duration_seconds=result.duration_seconds or 0,
                        sources_succeeded=result.sources_succeeded,
                        sources_failed=result.sources_failed,
                        records_stored=result.records_stored,
                        forecasts_generated=result.forecasts_generated,
                        execution_type='scheduled',
                        db=db,
                        next_run_time=next_run_str,
                        per_source_records=result.per_source_records,
                    )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Scheduled execution failed: {e}", exc_info=True)
        
        # Try to send alert
        if alert_service_config:
            try:
                alert_service = AlertService(
                    email_enabled=alert_service_config.get('email_enabled', False),
                    slack_enabled=alert_service_config.get('slack_enabled', False)
                )
                alert_service.send_pipeline_failure(
                    execution_id='scheduled',
                    error=e
                )
            except:
                pass  # Don't fail if alert fails


class PipelineScheduler:
    """
    Schedules and manages automated pipeline execution.
    
    Uses APScheduler with persistent job store for reliable scheduling.
    """
    
    def __init__(
        self,
        db_url: str,
        schedule: str = "0 6 * * *",  # Daily at 06:00 EAT
        timezone: str = "UTC",
        alert_service: Optional[AlertService] = None
    ):
        """
        Initialize pipeline scheduler
        
        Args:
            db_url: Database URL (used for clearing stale locks on startup)
            schedule: Cron expression for schedule (default: daily at 06:00 UTC)
            timezone: Timezone for scheduling (default: UTC)
            alert_service: Optional alert service for notifications
        """
        self.db_url = db_url
        self.schedule = schedule
        self.timezone = timezone
        self.alert_service = alert_service
        
        # Clear any stale advisory locks from previous container runs
        self._clear_stale_locks()
        
        # Use IN-MEMORY job store — no persistence needed.
        # The job is re-added on every startup. Persistent store
        # causes phantom runs from stale next_run_times after restarts.
        self.scheduler = BackgroundScheduler(
            timezone=timezone
        )
        
        self._job_id = 'pipeline_execution'
        logger.info(f"Pipeline scheduler initialized with schedule: {schedule}")
    
    def _clear_stale_locks(self) -> None:
        """Clear any stale advisory locks from previous container runs.
        
        On startup, terminate any PostgreSQL backends still holding
        advisory lock 123456 from old crashed/restarted containers.
        """
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_locks WHERE locktype = 'advisory' AND objid = 123456"
                ))
                terminated = result.fetchall()
                if terminated:
                    logger.info(f"Cleared {len(terminated)} stale advisory lock(s) on startup")
                else:
                    logger.info("No stale advisory locks found on startup")
                conn.commit()
            engine.dispose()
        except Exception as e:
            logger.warning(f"Failed to clear stale locks (non-fatal): {e}")
    
    def start(self) -> None:
        """
        Start the scheduler.
        
        Uses in-memory job store — job is added fresh on every startup.
        No persistent state, no phantom runs.
        """
        try:
            self.scheduler.add_job(
                func=execute_pipeline_standalone,
                trigger=CronTrigger.from_crontab(self.schedule, timezone=self.timezone),
                id=self._job_id,
                name='Automated Pipeline Execution',
                max_instances=1,
                coalesce=True,
                misfire_grace_time=1,      # Drop missed triggers
                kwargs={'alert_service_config': self._get_alert_config()}
            )
            logger.info(f"Added pipeline job with schedule: {self.schedule}")
        
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Pipeline scheduler started")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise
    
    def _get_alert_config(self) -> Optional[dict]:
        """Get serializable alert service configuration"""
        if not self.alert_service:
            return None
        # Return config that can be used to recreate alert service
        return {
            'email_enabled': getattr(self.alert_service, 'email_enabled', False),
            'slack_enabled': getattr(self.alert_service, 'slack_enabled', False),
            'slack_webhook_url': getattr(self.alert_service, 'slack_webhook_url', None),
        }
    
    def stop(self) -> None:
        """
        Gracefully stop the scheduler
        
        Waits for running jobs to complete before shutting down.
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Pipeline scheduler stopped")
            else:
                logger.info("Pipeline scheduler not running")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
    
    def trigger_manual_run(self, db: Session) -> ExecutionResult:
        """
        Manually trigger pipeline execution
        
        Args:
            db: Database session
            
        Returns:
            ExecutionResult with execution summary
        """
        logger.info("Manual pipeline execution triggered")
        
        try:
            orchestrator = PipelineOrchestrator(db, self.alert_service)
            result = orchestrator.execute_pipeline(execution_type='manual')
            
            logger.info(
                f"Manual execution completed: {result.status}, "
                f"execution_id={result.execution_id}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Manual execution failed: {e}", exc_info=True)
            
            # Send alert if available
            if self.alert_service:
                self.alert_service.send_pipeline_failure(
                    execution_id='manual',
                    error=e
                )
            
            raise
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get next scheduled execution time
        
        Returns:
            Next run time or None if job not scheduled
        """
        job = self.scheduler.get_job(self._job_id)
        if job and job.next_run_time:
            return job.next_run_time
        return None
    

