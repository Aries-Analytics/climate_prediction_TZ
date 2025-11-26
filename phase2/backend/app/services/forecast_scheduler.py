"""
Automated forecast scheduler service

Runs daily or when new climate data arrives to generate forecasts
for all trigger types and horizons.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.climate_data import ClimateData
from app.models.forecast import Forecast
from app.services.forecast_service import generate_forecasts, generate_all_recommendations

logger = logging.getLogger(__name__)


class ForecastScheduler:
    """Scheduler for automated forecast generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.last_run: Optional[datetime] = None
        self.horizons = [3, 4, 5, 6]  # Forecast horizons in months
    
    def should_run_forecast(self) -> bool:
        """
        Determine if forecast generation should run
        
        Returns True if:
        1. No forecasts exist yet, OR
        2. Latest forecast is older than 7 days, OR
        3. New climate data has arrived since last forecast
        """
        # Check if any forecasts exist
        latest_forecast = self.db.query(Forecast).order_by(
            Forecast.created_at.desc()
        ).first()
        
        if not latest_forecast:
            logger.info("No forecasts found - triggering generation")
            return True
        
        # Check if forecasts are older than 7 days
        days_old = (datetime.now() - latest_forecast.created_at).days
        if days_old >= 7:
            logger.info(f"Forecasts are {days_old} days old - triggering generation")
            return True
        
        # Check if new climate data has arrived
        latest_climate = self.db.query(ClimateData).order_by(
            ClimateData.date.desc()
        ).first()
        
        if latest_climate and latest_climate.date > latest_forecast.forecast_date:
            logger.info(f"New climate data available ({latest_climate.date}) - triggering generation")
            return True
        
        logger.info("Forecasts are up to date - skipping generation")
        return False
    
    def run_scheduled_forecast(self) -> dict:
        """
        Run scheduled forecast generation
        
        Returns:
            dict: Summary of forecast generation results
        """
        start_time = datetime.now()
        logger.info(f"Starting scheduled forecast generation at {start_time}")
        
        try:
            # Check if we should run
            if not self.should_run_forecast():
                return {
                    "status": "skipped",
                    "reason": "Forecasts are up to date",
                    "timestamp": start_time.isoformat()
                }
            
            # Generate forecasts
            forecasts = generate_forecasts(
                db=self.db,
                start_date=date.today(),
                horizons=self.horizons
            )
            
            if not forecasts:
                logger.error("Forecast generation failed - no forecasts created")
                return {
                    "status": "failed",
                    "reason": "No forecasts generated - insufficient data",
                    "timestamp": start_time.isoformat()
                }
            
            # Generate recommendations for high-probability forecasts
            recommendations = generate_all_recommendations(
                db=self.db,
                min_probability=0.3
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Forecast generation completed: {len(forecasts)} forecasts, "
                f"{len(recommendations)} recommendations in {duration:.2f}s"
            )
            
            self.last_run = end_time
            
            return {
                "status": "success",
                "forecasts_generated": len(forecasts),
                "recommendations_generated": len(recommendations),
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forecast generation failed with error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        Calculate when the next forecast generation should run
        
        Returns:
            datetime: Next scheduled run time (tomorrow at midnight)
        """
        if self.last_run:
            # Run daily - next run is tomorrow at midnight
            next_run = (self.last_run + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            # First run - schedule for tomorrow at midnight
            next_run = (datetime.now() + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        
        return next_run


def run_forecast_job(db: Session) -> dict:
    """
    Convenience function to run forecast generation job
    
    Args:
        db: Database session
        
    Returns:
        dict: Job execution summary
    """
    scheduler = ForecastScheduler(db)
    return scheduler.run_scheduled_forecast()
