"""
Mock ERA5 API - Copernicus Reanalysis Data

Simulates Copernicus Climate Data Store API for ERA5 reanalysis data.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .mock_base import BaseMockAPI, MockDataGenerator


class MockERA5API(BaseMockAPI):
    """
    Mock implementation of Copernicus CDS ERA5 API.

    Simulates reanalysis data including temperature, wind, and pressure.
    """

    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False):
        super().__init__(fail_rate, slow_response)

    def get_data(
        self,
        start_year: int,
        end_year: int,
        bounds: Optional[Dict[str, float]] = None,
        variables: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Get mock ERA5 reanalysis data.

        Args:
            start_year: Start year
            end_year: End year
            bounds: Geographic bounds
            variables: List of variable names

        Returns:
            DataFrame with ERA5 variables
        """
        self.record_call()
        self.simulate_delay()

        if self.simulate_failure():
            from .mock_base import MockAPIError

            raise MockAPIError("ERA5 CDS request failed", status_code=500)

        # Default variables
        if variables is None:
            variables = ["temperature_2m", "u_wind_10m", "v_wind_10m", "surface_pressure"]

        # Generate monthly data
        dates = MockDataGenerator.create_date_range(start_year, end_year, freq="MS")

        df = pd.DataFrame({"date": dates})

        # Generate each variable
        for var in variables:
            df[var] = self._generate_variable(var, dates)

        df["source"] = "ERA5"

        # Add missing data
        df = MockDataGenerator.apply_missing_data(df, missing_rate=0.002, columns=variables)

        return df

    def _generate_variable(self, variable: str, dates: pd.DatetimeIndex) -> np.ndarray:
        """Generate realistic ERA5 variable data."""
        if "temperature" in variable:
            # Temperature pattern (similar to NASA POWER but slightly different)
            temp = MockDataGenerator.generate_seasonal_pattern(dates, base_value=24.5, amplitude=3.5, peaks=[1, 10])
            temp = MockDataGenerator.add_noise(temp, noise_std=1.2)
            return temp

        elif "wind" in variable:
            # Wind components
            base = 2.0 if "u_wind" in variable else 1.5
            wind = MockDataGenerator.generate_seasonal_pattern(dates, base_value=base, amplitude=1.5, peaks=[7, 8])
            wind = MockDataGenerator.add_noise(wind, noise_std=0.6)
            return wind

        elif "pressure" in variable:
            # Surface pressure (relatively stable)
            pressure = MockDataGenerator.generate_seasonal_pattern(dates, base_value=1013.0, amplitude=5.0, peaks=[7])
            pressure = MockDataGenerator.add_noise(pressure, noise_std=2.0)
            return pressure

        else:
            # Generic
            return np.random.normal(50, 10, len(dates))


def get_mock_era5(**kwargs) -> MockERA5API:
    """Get a mock ERA5 API instance."""
    return MockERA5API(**kwargs)
