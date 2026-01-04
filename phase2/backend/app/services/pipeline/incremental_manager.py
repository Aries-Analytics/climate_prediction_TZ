"""
Incremental Ingestion Manager

Manages incremental data fetching by tracking last successful ingestion dates
per data source and calculating appropriate fetch ranges.
"""
import logging
from datetime import date, timedelta
from typing import Optional, NamedTuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.climate_data import ClimateData
from app.models.pipeline_execution import SourceIngestionTracking

logger = logging.getLogger(__name__)


class DateRange(NamedTuple):
    """Date range for data fetching"""
    start_date: date
    end_date: date


class IncrementalIngestionManager:
    """
    Manages incremental data ingestion by tracking last successful dates
    and calculating appropriate fetch ranges for each data source.
    """
    
    DEFAULT_LOOKBACK_DAYS = 180
    
    def __init__(self, db: Session):
        """
        Initialize the incremental ingestion manager
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_last_ingestion_date(self, source: str) -> Optional[date]:
        """
        Query database for most recent data date for a source
        
        Args:
            source: Data source name (e.g., 'chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices')
            
        Returns:
            Last successful ingestion date or None if no previous data exists
        """
        # First check the tracking table
        tracking = self.db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        
        if tracking:
            logger.info(f"Found tracking record for {source}: {tracking.last_successful_date}")
            return tracking.last_successful_date
        
        # Fall back to querying actual climate data
        # This handles the case where tracking table doesn't exist yet
        last_record = self.db.query(func.max(ClimateData.date)).scalar()
        
        if last_record:
            logger.info(f"Found last climate data record for {source}: {last_record}")
            return last_record
        
        logger.info(f"No previous data found for {source}")
        return None
    
    def calculate_fetch_range(self, source: str, end_date: Optional[date] = None) -> DateRange:
        """
        Calculate start/end dates for incremental fetch
        
        Args:
            source: Data source name
            end_date: End date for fetch (defaults to today)
            
        Returns:
            DateRange with start and end dates
        """
        if end_date is None:
            end_date = date.today()
        
        last_date = self.get_last_ingestion_date(source)
        
        if last_date is None:
            # No previous data, fetch default lookback period
            start_date = end_date - timedelta(days=self.DEFAULT_LOOKBACK_DAYS)
            logger.info(
                f"No previous data for {source}, fetching {self.DEFAULT_LOOKBACK_DAYS} days: "
                f"{start_date} to {end_date}"
            )
        else:
            # Incremental: fetch from last date + 1 day
            start_date = last_date + timedelta(days=1)
            logger.info(
                f"Incremental fetch for {source}: {start_date} to {end_date}"
            )
        
        return DateRange(start_date=start_date, end_date=end_date)
    
    def mark_ingestion_complete(
        self, 
        source: str, 
        end_date: date,
        execution_id: Optional[str] = None
    ) -> None:
        """
        Record successful ingestion completion
        
        Args:
            source: Data source name
            end_date: Last date successfully ingested
            execution_id: Pipeline execution ID (optional)
        """
        tracking = self.db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        
        if tracking:
            # Update existing record
            tracking.last_successful_date = end_date
            tracking.last_execution_id = execution_id
            logger.info(f"Updated tracking for {source}: {end_date}")
        else:
            # Create new record
            tracking = SourceIngestionTracking(
                source=source,
                last_successful_date=end_date,
                last_execution_id=execution_id
            )
            self.db.add(tracking)
            logger.info(f"Created tracking record for {source}: {end_date}")
        
        self.db.commit()
    
    def get_all_source_status(self) -> dict:
        """
        Get ingestion status for all sources
        
        Returns:
            Dictionary mapping source names to last ingestion dates
        """
        sources = ['chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices']
        status = {}
        
        for source in sources:
            last_date = self.get_last_ingestion_date(source)
            status[source] = {
                'last_date': last_date,
                'days_old': (date.today() - last_date).days if last_date else None
            }
        
        return status
    
    def needs_update(self, source: str, staleness_threshold_days: int = 7) -> bool:
        """
        Check if a source needs updating based on staleness threshold
        
        Args:
            source: Data source name
            staleness_threshold_days: Maximum age in days before update needed
            
        Returns:
            True if source needs updating, False otherwise
        """
        last_date = self.get_last_ingestion_date(source)
        
        if last_date is None:
            return True  # No data, definitely needs update
        
        days_old = (date.today() - last_date).days
        needs_update = days_old >= staleness_threshold_days
        
        if needs_update:
            logger.info(f"Source {source} is {days_old} days old, needs update")
        else:
            logger.info(f"Source {source} is {days_old} days old, up to date")
        
        return needs_update
