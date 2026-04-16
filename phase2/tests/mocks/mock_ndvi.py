"""
Mock NDVI API - Google Earth Engine Vegetation Index Data

Simulates Google Earth Engine MODIS and AVHRR NDVI data.
"""

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .mock_base import BaseMockAPI, MockDataGenerator, MockResponseBuilder


class MockNDVIAPI(BaseMockAPI):
    """
    Mock implementation of Google Earth Engine NDVI API.

    Simulates MODIS (2000+) and AVHRR (1985-1999) vegetation indices.
    """

    # NDVI characteristics for Tanzania
    BASE_NDVI = 0.5  # Baseline vegetation index
    SEASONAL_AMP = 0.2  # Seasonal variation

    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False):
        super().__init__(fail_rate, slow_response)

    def get_data(
        self, start_year: int, end_year: int, bounds: Optional[Dict[str, float]] = None, use_gee: bool = True
    ) -> pd.DataFrame:
        """
        Get mock NDVI data.

        Args:
            start_year: Start year
            end_year: End year
            bounds: Geographic bounds
            use_gee: If True, simulate GEE (otherwise synthetic)

        Returns:
            DataFrame with NDVI values
        """
        self.record_call()
        self.simulate_delay()

        if self.simulate_failure():
            from .mock_base import MockAPIError

            raise MockAPIError("NDVI data retrieval failed", status_code=500)

        # Monthly NDVI
        dates = MockDataGenerator.create_date_range(start_year, end_year, freq="MS")

        # Generate NDVI pattern
        ndvi = self._generate_ndvi_pattern(dates, start_year, end_year)

        df = pd.DataFrame(
            {
                "date": dates,
                "ndvi": ndvi,
                "source": "MODIS" if start_year >= 2000 else "AVHRR",
                "data_type": "vegetation_index",
            }
        )

        # Add missing data (clouds, etc.)
        df = MockDataGenerator.apply_missing_data(df, missing_rate=0.03, columns=["ndvi"])

        return df

    def _generate_ndvi_pattern(self, dates: pd.DatetimeIndex, start_year: int, end_year: int) -> np.ndarray:
        """Generate realistic NDVI pattern following vegetation cycles."""
        # Seasonal pattern (greening during rainy seasons)
        ndvi = MockDataGenerator.generate_seasonal_pattern(
            dates, base_value=self.BASE_NDVI, amplitude=self.SEASONAL_AMP, peaks=[4, 11]  # Greening during rain seasons
        )

        # Add interannual trend (slight greening over time)
        years = dates.year
        trend = 0.001 * (years - start_year)
        ndvi = ndvi + trend

        # Add noise
        ndvi = MockDataGenerator.add_noise(ndvi, noise_std=0.03)

        # Constrain to valid NDVI range
        return np.clip(ndvi, 0.0, 0.95)

    def get_image_collection(
        self, start_date: str, end_date: str, bounds: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """Get mock Earth Engine ImageCollection for NDVI."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        df = self.get_data(start.year, end.year, bounds)
        df = df[(df["date"] >= start) & (df["date"] <= end)]

        return MockResponseBuilder.build_gee_image_collection(
            df, date_column="date", value_column="ndvi", band_name="NDVI"
        )


def get_mock_ndvi(**kwargs) -> MockNDVIAPI:
    """Get a mock NDVI API instance."""
    return MockNDVIAPI(**kwargs)
