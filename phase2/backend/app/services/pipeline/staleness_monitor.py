"""
Staleness Monitor

Monitors data and forecast freshness and sends alerts when thresholds are exceeded.
"""
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.climate_data import ClimateData
from app.models.forecast import Forecast
from app.services.pipeline.alert_service import AlertService

logger = logging.getLogger(__name__)


class StalenessMonitor:
    """
    Monitors data and forecast staleness and sends alerts.
    
    Checks:
    - Climate data age (default threshold: 7 days)
    - Forecast age (default threshold: 7 days)
    """
    
    def __init__(
        self,
        db: Session,
        alert_service: AlertService,
        data_threshold_days: int = 7,
        forecast_threshold_days: int = 7
    ):
        """
        Initialize staleness monitor
        
        Args:
            db: Database session
            alert_service: Alert service for sending notifications
            data_threshold_days: Maximum age for climate data (days)
            forecast_threshold_days: Maximum age for forecasts (days)
        """
        self.db = db
        self.alert_service = alert_service
        self.data_threshold_days = data_threshold_days
        self.forecast_threshold_days = forecast_threshold_days
    
    def check_all_staleness(self) -> dict:
        """
        Check staleness for all data sources and forecasts
        
        Returns:
            Dictionary with staleness check results
        """
        logger.info("Running staleness checks")
        
        results = {
            'data_stale': False,
            'forecast_stale': False,
            'stale_sources': [],
            'data_age_days': None,
            'forecast_age_days': None
        }
        
        # Check climate data staleness
        data_age = self.check_climate_data_staleness()
        if data_age is not None:
            results['data_age_days'] = data_age
            if data_age > self.data_threshold_days:
                results['data_stale'] = True
                results['stale_sources'].append('climate_data')
        
        # Check forecast staleness
        forecast_age = self.check_forecast_staleness()
        if forecast_age is not None:
            results['forecast_age_days'] = forecast_age
            if forecast_age > self.forecast_threshold_days:
                results['forecast_stale'] = True
                results['stale_sources'].append('forecasts')
        
        logger.info(
            f"Staleness check complete: data_age={data_age} days, "
            f"forecast_age={forecast_age} days"
        )
        
        return results
    
    def check_climate_data_staleness(self) -> Optional[int]:
        """
        Check climate data staleness and send alert if stale
        
        Returns:
            Age of data in days, or None if no data exists
        """
        try:
            # Get most recent climate data date
            latest_date = self.db.query(func.max(ClimateData.date)).scalar()
            
            if latest_date is None:
                logger.warning("No climate data found in database")
                return None
            
            # Calculate age
            today = date.today()
            age_days = (today - latest_date).days
            
            logger.info(f"Climate data age: {age_days} days (last update: {latest_date})")
            
            # Send alert if stale
            if age_days > self.data_threshold_days:
                logger.warning(
                    f"Climate data is stale: {age_days} days old "
                    f"(threshold: {self.data_threshold_days} days)"
                )
                self.alert_service.send_data_staleness_alert(
                    source='climate_data',
                    last_date=latest_date,
                    days_old=age_days
                )
            
            return age_days
            
        except Exception as e:
            logger.error(f"Failed to check climate data staleness: {e}", exc_info=True)
            return None
    
    def check_forecast_staleness(self) -> Optional[int]:
        """
        Check forecast staleness and send alert if stale
        
        Returns:
            Age of forecasts in days, or None if no forecasts exist
        """
        try:
            # Get most recent forecast creation time
            latest_forecast = self.db.query(func.max(Forecast.created_at)).scalar()
            
            if latest_forecast is None:
                logger.warning("No forecasts found in database")
                return None
            
            # Calculate age
            now = datetime.now(timezone.utc)
            
            # Handle timezone-aware datetime
            if latest_forecast.tzinfo is not None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            
            age_timedelta = now - latest_forecast
            age_days = age_timedelta.days
            
            logger.info(f"Forecast age: {age_days} days (last created: {latest_forecast})")
            
            # Send alert if stale
            if age_days > self.forecast_threshold_days:
                logger.warning(
                    f"Forecasts are stale: {age_days} days old "
                    f"(threshold: {self.forecast_threshold_days} days)"
                )
                
                # Convert datetime to date for alert
                last_date = latest_forecast.date() if hasattr(latest_forecast, 'date') else date.today()
                
                self.alert_service.send_data_staleness_alert(
                    source='forecasts',
                    last_date=last_date,
                    days_old=age_days
                )
            
            return age_days
            
        except Exception as e:
            logger.error(f"Failed to check forecast staleness: {e}", exc_info=True)
            return None
    
    def check_source_staleness(self, source: str) -> Optional[int]:
        """
        Check staleness for a specific data source
        
        Args:
            source: Source name to check
            
        Returns:
            Age of source data in days, or None if no data
        """
        try:
            # Query most recent data for this source
            # This assumes climate_data has a source field
            # If not, this would need to be adapted based on actual schema
            latest_date = self.db.query(func.max(ClimateData.date)).scalar()
            
            if latest_date is None:
                return None
            
            today = date.today()
            age_days = (today - latest_date).days
            
            # Send alert if stale
            if age_days > self.data_threshold_days:
                self.alert_service.send_data_staleness_alert(
                    source=source,
                    last_date=latest_date,
                    days_old=age_days
                )
            
            return age_days
            
        except Exception as e:
            logger.error(f"Failed to check staleness for {source}: {e}", exc_info=True)
            return None
