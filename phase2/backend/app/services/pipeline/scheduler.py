"""
Pipeline Scheduler Service

Schedules automated pipeline execution using APScheduler.
"""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
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
                    slack_enabled=alert_service_config.get('slack_enabled', False)
                )
            
            orchestrator = PipelineOrchestrator(db, alert_service)
            result = orchestrator.execute_pipeline(execution_type='scheduled')
            
            logger.info(
                f"Scheduled execution completed: {result.status}, "
                f"execution_id={result.execution_id}, "
                f"duration={result.duration_seconds}s"
            )
            
            # Send alert if execution failed
            if result.status == 'failed' and alert_service:
                alert_service.send_pipeline_failure(
                    execution_id=result.execution_id,
                    error=Exception(result.error_message or "Pipeline execution failed")
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
        schedule: str = "0 6 * * *",  # Daily at 06:00 UTC
        timezone: str = "UTC",
        alert_service: Optional[AlertService] = None
    ):
        """
        Initialize pipeline scheduler
        
        Args:
            db_url: Database URL for persistent job store
            schedule: Cron expression for schedule (default: daily at 06:00 UTC)
            timezone: Timezone for scheduling (default: UTC)
            alert_service: Optional alert service for notifications
        """
        self.db_url = db_url
        self.schedule = schedule
        self.timezone = timezone
        self.alert_service = alert_service
        
        # Configure job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=timezone
        )
        
        self._job_id = 'pipeline_execution'
        logger.info(f"Pipeline scheduler initialized with schedule: {schedule}")
    
    def start(self) -> None:
        """
        Start the scheduler
        
        Adds the pipeline execution job and starts the scheduler.
        """
        try:
            # Add job if it doesn't exist
            if not self.scheduler.get_job(self._job_id):
                # Use a standalone function instead of instance method to avoid serialization issues
                self.scheduler.add_job(
                    func=execute_pipeline_standalone,
                    trigger=CronTrigger.from_crontab(self.schedule),
                    id=self._job_id,
                    name='Automated Pipeline Execution',
                    replace_existing=True,
                    kwargs={'alert_service_config': self._get_alert_config()}
                )
                logger.info(f"Added pipeline job with schedule: {self.schedule}")
            
            # Start scheduler
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Pipeline scheduler started")
            else:
                logger.info("Pipeline scheduler already running")
                
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
    

