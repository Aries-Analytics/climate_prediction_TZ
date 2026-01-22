"""
Mock API Base Classes and Utilities

Provides base infrastructure for all mock API implementations used in integration testing.
This allows tests to run without making actual network calls to external services.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class BaseMockAPI(ABC):
    """
    Abstract base class for all mock API implementations.
    
    Mock APIs simulate external data sources without making network calls,
    enabling fast, reliable, and reproducible integration tests.
    """
    
    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False):
        """
        Initialize mock API.
        
        Args:
            fail_rate: Probability of simulating API failure (0.0 to 1.0)
            slow_response: If True, simulate slow network responses
        """
        self.fail_rate = fail_rate
        self.slow_response = slow_response
        self.call_count = 0
        self.last_call_time = None
    
    def simulate_failure(self) -> bool:
        """Check if this call should simulate a failure."""
        return np.random.random() < self.fail_rate
    
    def simulate_delay(self):
        """Simulate network delay if configured."""
        if self.slow_response:
            import time
            time.sleep(np.random.uniform(0.5, 2.0))
    
    def record_call(self):
        """Record API call for debugging/testing."""
        self.call_count += 1
        self.last_call_time = datetime.now()
    
    @abstractmethod
    def get_data(self, *args, **kwargs) -> Any:
        """
        Get mock data. Must be implemented by subclasses.
        
        Returns:
            Mock data in the format expected by the real API
        """
        pass


class MockDataGenerator:
    """
    Utilities for generating realistic climate data with proper statistical properties.
    """
    
    @staticmethod
    def generate_seasonal_pattern(
        dates: pd.DatetimeIndex,
        base_value: float,
        amplitude: float,
        peaks: List[int]
    ) -> np.ndarray:
        """
        Generate seasonal pattern with specified peaks.
        
        Args:
            dates: Date range for data generation
            base_value: Baseline value
            amplitude: Seasonal variation amplitude
            peaks: List of peak months (1-12)
        
        Returns:
            Array of values with seasonal pattern
        """
        months = dates.month
        seasonal = np.zeros(len(dates))
        
        for peak_month in peaks:
            # Create a seasonal wave centered on peak month
            phase = (months - peak_month) * (2 * np.pi / 12)
            seasonal += np.cos(phase)
        
        # Normalize to 0-1 range
        seasonal = (seasonal - seasonal.min()) / (seasonal.max() - seasonal.min())
        
        # Scale to desired amplitude and add base value
        return base_value + (seasonal - 0.5) * amplitude
    
    @staticmethod
    def add_noise(
        values: np.ndarray,
        noise_std: float,
        distribution: str = "normal"
    ) -> np.ndarray:
        """
        Add realistic noise to data.
        
        Args:
            values: Base values
            noise_std: Standard deviation of noise
            distribution: "normal", "lognormal", or "uniform"
        
        Returns:
            Values with added noise
        """
        if distribution == "normal":
            noise = np.random.normal(0, noise_std, len(values))
        elif distribution == "lognormal":
            noise = np.random.lognormal(0, noise_std, len(values)) - 1
        elif distribution == "uniform":
            noise = np.random.uniform(-noise_std, noise_std, len(values))
        else:
            raise ValueError(f"Unknown distribution: {distribution}")
        
        return values + noise
    
    @staticmethod
    def add_extreme_events(
        values: np.ndarray,
        event_probability: float,
        event_magnitude: float
    ) -> np.ndarray:
        """
        Add random extreme events (droughts, floods, heatwaves).
        
        Args:
            values: Base values
            event_probability: Probability of extreme event per time step
            event_magnitude: Magnitude of extreme events (multiplier)
        
        Returns:
            Values with extreme events added
        """
        events = np.random.random(len(values)) < event_probability
        multipliers = np.where(
            events,
            np.random.choice([0.3, 2.5], len(values)),  # Drought or flood
            1.0
        )
        return values * multipliers
    
    @staticmethod
    def generate_autocorrelated_noise(
        length: int,
        autocorr: float = 0.7,
        std: float = 1.0
    ) -> np.ndarray:
        """
        Generate autocorrelated (time-dependent) noise.
        
        Args:
            length: Number of time steps
            autocorr: Autocorrelation coefficient (0-1)
            std: Standard deviation
        
        Returns:
            Autocorrelated noise series
        """
        noise = np.zeros(length)
        noise[0] = np.random.normal(0, std)
        
        for i in range(1, length):
            noise[i] = (
                autocorr * noise[i-1] +
                np.random.normal(0, std * np.sqrt(1 - autocorr**2))
            )
        
        return noise
    
    @staticmethod
    def create_date_range(
        start_year: int,
        end_year: int,
        freq: str = "MS"  # Month start
    ) -> pd.DatetimeIndex:
        """
        Create a date range for data generation.
        
        Args:
            start_year: Start year
            end_year: End year
            freq: Pandas frequency string (MS=month start, D=daily)
        
        Returns:
            DatetimeIndex covering the specified range
        """
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        return pd.date_range(start=start_date, end=end_date, freq=freq)
    
    @staticmethod
    def apply_missing_data(
        df: pd.DataFrame,
        missing_rate: float = 0.02,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Randomly introduce missing values to simulate real-world data gaps.
        
        Args:
            df: DataFrame to modify
            missing_rate: Fraction of values to set as missing
            columns: Columns to apply missing data to (None = all numeric columns)
        
        Returns:
            DataFrame with missing values introduced
        """
        df = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        for col in columns:
            mask = np.random.random(len(df)) < missing_rate
            df.loc[mask, col] = np.nan
        
        return df


class MockResponseBuilder:
    """
    Helpers for building API-like responses.
    """
    
    @staticmethod
    def build_json_response(
        data: Dict[str, Any],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Build a mock HTTP JSON response.
        
        Args:
            data: Response data
            status_code: HTTP status code
            headers: HTTP headers
        
        Returns:
            Mock response dictionary
        """
        return {
            "status_code": status_code,
            "headers": headers or {"Content-Type": "application/json"},
            "data": data
        }
    
    @staticmethod
    def build_error_response(
        error_message: str,
        status_code: int = 500,
        error_type: str = "InternalServerError"
    ) -> Dict[str, Any]:
        """
        Build a mock error response.
        
        Args:
            error_message: Error message
            status_code: HTTP status code
            error_type: Error type/class
        
        Returns:
            Mock error response
        """
        return {
            "status_code": status_code,
            "error": {
                "type": error_type,
                "message": error_message
            }
        }
    
    @staticmethod
    def build_gee_image_collection(
        df: pd.DataFrame,
        date_column: str = "date",
        value_column: str = "value",
        band_name: str = "data"
    ) -> List[Dict[str, Any]]:
        """
        Build a mock Google Earth Engine ImageCollection structure.
        
        Args:
            df: DataFrame with data
            date_column: Name of date column
            value_column: Name of value column
            band_name: Name of the band
        
        Returns:
            List of mock images
        """
        images = []
        
        for _, row in df.iterrows():
            images.append({
                "type": "Image",
                "id": f"mock_image_{row[date_column].strftime('%Y%m%d')}",
                "properties": {
                    "system:time_start": int(row[date_column].timestamp() * 1000),
                    "system:index": row[date_column].strftime('%Y%m%d')
                },
                "bands": [{
                    "id": band_name,
                    "data_type": "float",
                    "crs": "EPSG:4326"
                }],
                "data": {band_name: row[value_column]}
            })
        
        return images


class MockAPIError(Exception):
    """Exception raised by mock APIs to simulate real API errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
