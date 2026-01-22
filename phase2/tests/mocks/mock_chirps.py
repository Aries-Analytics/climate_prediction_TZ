"""
Mock CHIRPS API - Google Earth Engine Rainfall Data

Simulates the Google Earth Engine CHIRPS dataset for integration testing.
Generates realistic bimodal rainfall patterns typical of Tanzania.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .mock_base import BaseMockAPI, MockDataGenerator, MockResponseBuilder


class MockCHIRPSAPI(BaseMockAPI):
    """
    Mock implementation of Google Earth Engine CHIRPS API.
    
    Simulates UCSB-CHG/CHIRPS/DAILY dataset with realistic Tanzania rainfall patterns.
    """
    
    # Tanzania rainfall characteristics (bimodal pattern)
    LONG_RAINS_PEAK = 4  # March-May (April peak)
    SHORT_RAINS_PEAK = 11  # October-December (November peak)
    BASE_RAINFALL = 50  # mm/month baseline
    SEASONAL_AMPLITUDE = 100  # mm/month variation
    
    def __init__(
        self,
        fail_rate: float = 0.0,
        slow_response: bool = False,
        locations: Optional[List[Dict[str, float]]] = None
    ):
        """
        Initialize mock CHIRPS API.
        
        Args:
            fail_rate: Probability of API failure
            slow_response: Simulate slow responses
            locations: List of location dicts with lat/lon bounds
        """
        super().__init__(fail_rate, slow_response)
        
        # Default to Tanzania bounding box if no locations provided
        self.locations = locations or [{
            "name": "Tanzania",
            "lat_min": -11.75,
            "lat_max": -0.99,
            "lon_min": 29.34,
            "lon_max": 40.44
        }]
    
    def get_data(
        self,
        start_year: int,
        end_year: int,
        bounds: Optional[Dict[str, float]] = None,
        aggregation: str = "monthly"
    ) -> pd.DataFrame:
        """
        Get mock CHIRPS rainfall data.
        
        Args:
            start_year: Start year for data
            end_year: End year for data
            bounds: Geographic bounding box
            aggregation: "daily" or "monthly"
        
        Returns:
            DataFrame with columns: date, rainfall_mm, location_name
        
        Raises:
            MockAPIError: If configured to fail
        """
        self.record_call()
        self.simulate_delay()
        
        if self.simulate_failure():
            from .mock_base import MockAPIError
            raise MockAPIError("CHIRPS data retrieval failed", status_code=500)
        
        # Use provided bounds or default
        location = bounds or self.locations[0]
        location_name = location.get("name", "Unknown")
        
        # Generate date range
        freq = "D" if aggregation == "daily" else "MS"
        dates = MockDataGenerator.create_date_range(start_year, end_year, freq=freq)
        
        # Generate realistic rainfall pattern
        rainfall = self._generate_rainfall_pattern(dates, location)
        
        # Create DataFrame
        df = pd.DataFrame({
            "date": dates,
            "rainfall_mm": rainfall,
            "location_name": location_name,
            "source": "CHIRPS",
            "data_type": "rainfall"
        })
        
        # Add some missing data (realistic)
        df = MockDataGenerator.apply_missing_data(df, missing_rate=0.01, columns=["rainfall_mm"])
        
        return df
    
    def _generate_rainfall_pattern(
        self,
        dates: pd.DatetimeIndex,
        location: Dict[str, float]
    ) -> np.ndarray:
        """
        Generate realistic bimodal rainfall pattern for Tanzania.
        
        Args:
            dates: Date range
            location: Location info (for spatial variation)
        
        Returns:
            Array of rainfall values in mm
        """
        # Base seasonal pattern (bimodal for Tanzania)
        seasonal = MockDataGenerator.generate_seasonal_pattern(
            dates,
            base_value=self.BASE_RAINFALL,
            amplitude=self.SEASONAL_AMPLITUDE,
            peaks=[self.LONG_RAINS_PEAK, self.SHORT_RAINS_PEAK]
        )
        
        # Add interannual variability (ENSO influence)
        years = dates.year
        enso_cycle = np.sin((years - years.min()) * 2 * np.pi / 3.5)  # ~3.5 year cycle
        interannual = 1.0 + 0.2 * enso_cycle
        
        rainfall = seasonal * interannual
        
        # Add autocorrelated noise (day-to-day persistence)
        noise = MockDataGenerator.generate_autocorrelated_noise(
            len(dates),
            autocorr=0.6,
            std=15
        )
        rainfall = rainfall + noise
        
        # Add extreme events (droughts and floods)
        rainfall = MockDataGenerator.add_extreme_events(
            rainfall,
            event_probability=0.05,
            event_magnitude=2.0
        )
        
        # Ensure non-negative (rainfall can't be negative)
        rainfall = np.maximum(rainfall, 0)
        
        # Add measurement noise
        rainfall = MockDataGenerator.add_noise(rainfall, noise_std=2.0, distribution="normal")
        
        return np.maximum(rainfall, 0)  # Ensure non-negative after noise
    
    def get_image_collection(
        self,
        start_date: str,
        end_date: str,
        bounds: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Get mock Earth Engine ImageCollection structure.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bounds: Geographic bounds
        
        Returns:
            List of mock EE images
        """
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get data
        df = self.get_data(start.year, end.year, bounds, aggregation="daily")
        
        # Filter to date range
        df = df[(df["date"] >= start) & (df["date"] <= end)]
        
        # Build GEE-like structure
        return MockResponseBuilder.build_gee_image_collection(
            df,
            date_column="date",
            value_column="rainfall_mm",
            band_name="precipitation"
        )


class MockCHIRPSMultiLocation(MockCHIRPSAPI):
    """
    Mock CHIRPS API supporting multiple locations.
    
    Generates location-specific rainfall patterns for calibrated locations.
    """
    
    # Pre-defined calibrated locations from actual dataset
    CALIBRATED_LOCATIONS = {
        "Morogoro (Kilombero Basin)": {
            "lat_min": -8.5, "lat_max": -7.5,
            "lon_min": 36.0, "lon_max": 37.0,
            "rainfall_multiplier": 1.2  # Wetter region
        },
        "Dodoma": {
            "lat_min": -6.5, "lat_max": -5.5,
            "lon_min": 35.5, "lon_max": 36.5,
            "rainfall_multiplier": 0.8  # Drier region
        },
        "Mwanza": {
            "lat_min": -3.0, "lat_max": -2.0,
            "lon_min": 32.5, "lon_max": 33.5,
            "rainfall_multiplier": 1.0  # Average
        },
        "Arusha": {
            "lat_min": -3.5, "lat_max": -3.0,
            "lon_min": 36.5, "lon_max": 37.0,
            "rainfall_multiplier": 0.9
        },
        "Mbeya": {
            "lat_min": -9.0, "lat_max": -8.5,
            "lon_min": 32.5, "lon_max": 33.5,
            "rainfall_multiplier": 1.1
        }
    }
    
    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False):
        """Initialize with calibrated locations."""
        locations = [
            {**loc, "name": name}
            for name, loc in self.CALIBRATED_LOCATIONS.items()
        ]
        super().__init__(fail_rate, slow_response, locations)
    
    def get_data_all_locations(
        self,
        start_year: int,
        end_year: int
    ) -> pd.DataFrame:
        """
        Get data for all calibrated locations.
        
        Args:
            start_year: Start year
            end_year: End year
        
        Returns:
            Combined DataFrame for all locations
        """
        all_data = []
        
        for location in self.locations:
            df = self.get_data(start_year, end_year, bounds=location)
            
            # Apply location-specific multiplier
            multiplier = location.get("rainfall_multiplier", 1.0)
            df["rainfall_mm"] = df["rainfall_mm"] * multiplier
            
            all_data.append(df)
        
        return pd.concat(all_data, ignore_index=True)


# Export mock instances for easy use in tests
def get_mock_chirps(multi_location: bool = False, **kwargs) -> MockCHIRPSAPI:
    """
    Get a mock CHIRPS API instance.
    
    Args:
        multi_location: If True, use multi-location mock
        **kwargs: Additional arguments for mock constructor
    
    Returns:
        Mock CHIRPS API instance
    """
    if multi_location:
        return MockCHIRPSMultiLocation(**kwargs)
    return MockCHIRPSAPI(**kwargs)
