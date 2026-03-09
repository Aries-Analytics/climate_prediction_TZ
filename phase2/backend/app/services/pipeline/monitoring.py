"""
Monitoring Service

Exposes metrics and health checks for pipeline monitoring.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, NamedTuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.pipeline_execution import PipelineExecution
from app.models.climate_data import ClimateData
from app.models.forecast import Forecast

logger = logging.getLogger(__name__)


class HealthStatus(NamedTuple):
    """Health status response"""
    status: str  # 'healthy' | 'degraded' | 'unhealthy'
    last_execution: Optional[datetime]
    data_freshness_days: Optional[int]
    forecast_freshness_days: Optional[int]
    failed_sources: list
    message: Optional[str] = None


class MonitoringService:
    """
    Monitoring service for pipeline health checks and metrics.
    
    Provides:
    - Health status endpoint
    - Prometheus-formatted metrics
    - Execution metrics recording
    """
    
    def __init__(self, db: Session):
        """
        Initialize monitoring service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_health_status(self) -> HealthStatus:
        """
        Get current system health status
        
        Returns:
            HealthStatus with current system state
        """
        try:
            # Get last execution
            last_execution = self.db.query(PipelineExecution).order_by(
                desc(PipelineExecution.started_at)
            ).first()
            
            # Calculate data freshness
            data_freshness_days = self._get_data_freshness_days()
            
            # Calculate forecast freshness
            forecast_freshness_days = self._get_forecast_freshness_days()
            
            # Get failed sources from last execution
            failed_sources = []
            if last_execution and last_execution.sources_failed:
                failed_sources = last_execution.sources_failed
            
            # Determine overall health status
            status = self._determine_health_status(
                last_execution,
                data_freshness_days,
                forecast_freshness_days,
                failed_sources
            )
            
            return HealthStatus(
                status=status,
                last_execution=last_execution.started_at if last_execution else None,
                data_freshness_days=data_freshness_days,
                forecast_freshness_days=forecast_freshness_days,
                failed_sources=failed_sources
            )
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}", exc_info=True)
            return HealthStatus(
                status='unhealthy',
                last_execution=None,
                data_freshness_days=None,
                forecast_freshness_days=None,
                failed_sources=[],
                message=f"Health check failed: {str(e)}"
            )
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Get Prometheus-formatted metrics
        
        Returns:
            Dictionary of metric names to values
        """
        try:
            metrics = {}
            
            # Pipeline execution metrics
            total_executions = self.db.query(func.count(PipelineExecution.id)).scalar() or 0
            metrics['pipeline_execution_total'] = float(total_executions)
            
            # Failure count
            failed_executions = self.db.query(func.count(PipelineExecution.id)).filter(
                PipelineExecution.status == 'failed'
            ).scalar() or 0
            metrics['pipeline_execution_failures_total'] = float(failed_executions)
            
            # Success rate
            if total_executions > 0:
                success_rate = (total_executions - failed_executions) / total_executions
                metrics['pipeline_execution_success_rate'] = success_rate
            else:
                metrics['pipeline_execution_success_rate'] = 0.0
            
            # Last execution duration
            last_execution = self.db.query(PipelineExecution).order_by(
                desc(PipelineExecution.started_at)
            ).first()
            
            if last_execution and last_execution.duration_seconds:
                metrics['pipeline_execution_duration_seconds'] = float(last_execution.duration_seconds)
            
            # Last success timestamp
            last_success = self.db.query(PipelineExecution).filter(
                PipelineExecution.status.in_(['completed', 'partial'])
            ).order_by(desc(PipelineExecution.completed_at)).first()
            
            if last_success and last_success.completed_at:
                metrics['pipeline_last_success_timestamp'] = float(last_success.completed_at.timestamp())
            
            # Data records ingested
            total_records = self.db.query(func.sum(PipelineExecution.records_stored)).scalar() or 0
            metrics['pipeline_data_records_ingested_total'] = float(total_records)
            
            # Forecasts generated
            total_forecasts = self.db.query(func.sum(PipelineExecution.forecasts_generated)).scalar() or 0
            metrics['pipeline_forecasts_generated_total'] = float(total_forecasts)
            
            # Data freshness
            data_freshness_days = self._get_data_freshness_days()
            if data_freshness_days is not None:
                metrics['data_freshness_days'] = float(data_freshness_days)
            
            # Forecast freshness
            forecast_freshness_days = self._get_forecast_freshness_days()
            if forecast_freshness_days is not None:
                metrics['forecast_freshness_days'] = float(forecast_freshness_days)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}", exc_info=True)
            return {}
    
    def record_execution_metrics(self, execution_id: str) -> None:
        """
        Record metrics for a pipeline execution
        
        Args:
            execution_id: Execution ID to record metrics for
        """
        try:
            execution = self.db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            
            if not execution:
                logger.warning(f"Execution {execution_id} not found for metrics recording")
                return
            
            logger.info(
                f"Recorded metrics for execution {execution_id}: "
                f"status={execution.status}, "
                f"duration={execution.duration_seconds}s, "
                f"records={execution.records_stored}, "
                f"forecasts={execution.forecasts_generated}"
            )
            
        except Exception as e:
            logger.error(f"Failed to record execution metrics: {e}", exc_info=True)
    
    def _get_data_freshness_days(self) -> Optional[int]:
        """
        Get age of most recent climate data in days
        
        Returns:
            Days since last data update, or None if no data
        """
        try:
            latest_date = self.db.query(func.max(ClimateData.date)).scalar()
            
            if latest_date:
                today = datetime.now(timezone.utc).date()
                freshness = (today - latest_date).days
                return freshness
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get data freshness: {e}")
            return None
    
    def _get_forecast_freshness_days(self) -> Optional[int]:
        """
        Get age of most recent forecast in days
        
        Returns:
            Days since last forecast, or None if no forecasts
        """
        try:
            latest_forecast = self.db.query(func.max(Forecast.created_at)).scalar()
            
            if latest_forecast:
                now = datetime.now(timezone.utc)
                # Handle timezone-naive datetime from database
                if latest_forecast.tzinfo is None:
                    latest_forecast = latest_forecast.replace(tzinfo=timezone.utc)

                freshness = (now - latest_forecast).days
                return freshness
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get forecast freshness: {e}")
            return None
    
    def _determine_health_status(
        self,
        last_execution: Optional[PipelineExecution],
        data_freshness_days: Optional[int],
        forecast_freshness_days: Optional[int],
        failed_sources: list
    ) -> str:
        """
        Determine overall health status based on metrics
        
        Args:
            last_execution: Last pipeline execution
            data_freshness_days: Age of data in days
            forecast_freshness_days: Age of forecasts in days
            failed_sources: List of failed sources
            
        Returns:
            Health status: 'healthy', 'degraded', or 'unhealthy'
        """
        # Unhealthy conditions
        if last_execution and last_execution.status == 'failed':
            return 'unhealthy'
        
        if data_freshness_days and data_freshness_days > 7:
            return 'unhealthy'
        
        if forecast_freshness_days and forecast_freshness_days > 7:
            return 'unhealthy'
        
        # Degraded conditions
        if failed_sources and len(failed_sources) > 0:
            return 'degraded'
        
        if data_freshness_days and data_freshness_days > 2:
            return 'degraded'
        
        if forecast_freshness_days and forecast_freshness_days > 2:
            return 'degraded'
        
        # Healthy
        return 'healthy'
    
    def format_prometheus_metrics(self, metrics: Dict[str, float]) -> str:
        """
        Format metrics in Prometheus text format
        
        Args:
            metrics: Dictionary of metric names to values
            
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        for metric_name, value in metrics.items():
            # Add metric type hint
            if 'total' in metric_name:
                lines.append(f"# TYPE {metric_name} counter")
            elif 'rate' in metric_name or 'freshness' in metric_name:
                lines.append(f"# TYPE {metric_name} gauge")
            elif 'duration' in metric_name:
                lines.append(f"# TYPE {metric_name} histogram")
            
            # Add metric value
            lines.append(f"{metric_name} {value}")
        
        return '\n'.join(lines)
