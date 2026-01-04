"""
Data Quality Validator

Validates ingested climate data for completeness, range validity, and gaps.
"""
import logging
import pandas as pd
from typing import List, NamedTuple, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class Anomaly(NamedTuple):
    """Data anomaly record"""
    field: str
    value: float
    expected_range: tuple
    date: Optional[date] = None


class DateRange(NamedTuple):
    """Date range for gaps"""
    start_date: date
    end_date: date


class ValidationResult(NamedTuple):
    """Result of data quality validation"""
    is_valid: bool
    missing_fields: List[str]
    anomalies: List[Anomaly]
    data_gaps: List[DateRange]
    quality_score: float
    total_records: int


class DataQualityValidator:
    """
    Validates climate data quality with configurable rules.
    
    Checks:
    - Required fields presence
    - Value range validation
    - Data gap detection
    - Quality score calculation
    """
    
    # Value range validation rules
    VALIDATION_RULES = {
        'temperature': (-50.0, 60.0),  # Celsius
        'rainfall': (0.0, 1000.0),     # mm per day
        'ndvi': (-1.0, 1.0),           # Normalized index
        'enso': (-3.0, 3.0),           # ENSO index
        'iod': (-2.0, 2.0),            # IOD index
    }
    
    REQUIRED_FIELDS = ['date']  # At least date must be present
    
    def validate_climate_data(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate climate data quality
        
        Args:
            df: DataFrame with climate data
            
        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {len(df)} climate data records")
        
        # Check required fields
        missing_fields = self.check_required_fields(df)
        
        # Check value ranges
        anomalies = self.check_value_ranges(df)
        
        # Detect data gaps
        data_gaps = self.detect_data_gaps(df)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            len(df),
            len(missing_fields),
            len(anomalies),
            len(data_gaps)
        )
        
        is_valid = quality_score >= 0.7  # 70% threshold
        
        logger.info(
            f"Validation complete: quality_score={quality_score:.2f}, "
            f"anomalies={len(anomalies)}, gaps={len(data_gaps)}"
        )
        
        return ValidationResult(
            is_valid=is_valid,
            missing_fields=missing_fields,
            anomalies=anomalies,
            data_gaps=data_gaps,
            quality_score=quality_score,
            total_records=len(df)
        )
    
    def check_required_fields(self, df: pd.DataFrame) -> List[str]:
        """
        Check for missing required fields
        
        Args:
            df: DataFrame to check
            
        Returns:
            List of missing field names
        """
        missing = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in df.columns:
                missing.append(field)
                logger.warning(f"Required field missing: {field}")
        
        # Check if at least one climate variable exists
        climate_vars = ['temperature', 'rainfall', 'ndvi', 'enso', 'iod']
        has_climate_var = any(var in df.columns for var in climate_vars)
        
        if not has_climate_var:
            missing.append('climate_variables')
            logger.warning("No climate variables found in data")
        
        return missing
    
    def check_value_ranges(self, df: pd.DataFrame) -> List[Anomaly]:
        """
        Check for out-of-range values
        
        Args:
            df: DataFrame to check
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for field, (min_val, max_val) in self.VALIDATION_RULES.items():
            if field not in df.columns:
                continue
            
            # Find out-of-range values
            out_of_range = df[
                (df[field].notna()) &
                ((df[field] < min_val) | (df[field] > max_val))
            ]
            
            for idx, row in out_of_range.iterrows():
                anomaly = Anomaly(
                    field=field,
                    value=float(row[field]),
                    expected_range=(min_val, max_val),
                    date=row.get('date')
                )
                anomalies.append(anomaly)
                logger.warning(
                    f"Anomaly detected: {field}={row[field]} "
                    f"(expected {min_val} to {max_val}) on {row.get('date')}"
                )
        
        return anomalies
    
    def detect_data_gaps(self, df: pd.DataFrame, max_gap_days: int = 7) -> List[DateRange]:
        """
        Detect missing date ranges
        
        Args:
            df: DataFrame with date column
            max_gap_days: Maximum gap size to report (default 7 days)
            
        Returns:
            List of date ranges with gaps
        """
        if 'date' not in df.columns or len(df) == 0:
            return []
        
        gaps = []
        
        # Sort by date
        df_sorted = df.sort_values('date')
        dates = pd.to_datetime(df_sorted['date']).dt.date.tolist()
        
        # Check for gaps between consecutive dates
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            # Calculate gap
            gap_days = (next_date - current_date).days - 1
            
            if gap_days >= max_gap_days:
                gap_range = DateRange(
                    start_date=current_date + timedelta(days=1),
                    end_date=next_date - timedelta(days=1)
                )
                gaps.append(gap_range)
                logger.warning(
                    f"Data gap detected: {gap_days} days between "
                    f"{current_date} and {next_date}"
                )
        
        return gaps
    
    def _calculate_quality_score(
        self,
        total_records: int,
        missing_fields_count: int,
        anomalies_count: int,
        gaps_count: int
    ) -> float:
        """
        Calculate overall quality score (0.0 to 1.0)
        
        Args:
            total_records: Total number of records
            missing_fields_count: Number of missing required fields
            anomalies_count: Number of anomalies detected
            gaps_count: Number of data gaps
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if total_records == 0:
            return 0.0
        
        # Start with perfect score
        score = 1.0
        
        # Penalize missing fields heavily (0.3 per field)
        score -= missing_fields_count * 0.3
        
        # Penalize anomalies (0.01 per anomaly, capped at 0.3)
        anomaly_penalty = min(0.3, (anomalies_count / total_records) * 0.5)
        score -= anomaly_penalty
        
        # Penalize gaps (0.05 per gap, capped at 0.2)
        gap_penalty = min(0.2, gaps_count * 0.05)
        score -= gap_penalty
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
