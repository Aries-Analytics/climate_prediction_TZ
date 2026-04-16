"""
Mock NASA POWER API - Climate Data

Simulates NASA POWER HTTP API for temperature, humidity, and solar radiation data.
Generates realistic climate patterns for Tanzania.
"""

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .mock_base import BaseMockAPI, MockDataGenerator, MockResponseBuilder


class MockNASAPowerAPI(BaseMockAPI):
    """
    Mock implementation of NASA POWER HTTP API.

    Simulates responses from power.larc.nasa.gov for climate variables.
    """

    # Tanzania climate characteristics
    BASE_TEMP = 25.0  # °C average temperature
    TEMP_SEASONAL_AMP = 3.0  # °C seasonal variation
    BASE_HUMIDITY = 65.0  # % average humidity
    HUMIDITY_SEASONAL_AMP = 15.0  # % seasonal variation
    BASE_SOLAR = 18.0  # MJ/m²/day
    SOLAR_SEASONAL_AMP = 3.0  # MJ/m²/day variation

    # Available parameters
    AVAILABLE_PARAMETERS = [
        "T2M",  # Temperature at 2m
        "T2M_MAX",  # Maximum temperature
        "T2M_MIN",  # Minimum temperature
        "RH2M",  # Relative humidity at 2m
        "PRECTOTCORR",  # Precipitation (corrected)
        "ALLSKY_SFC_SW_DWN",  # Solar radiation
        "WS2M",  # Wind speed at 2m
    ]

    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False, rate_limit: bool = False):
        """
        Initialize mock NASA POWER API.

        Args:
            fail_rate: Probability of API failure
            slow_response: Simulate slow responses
            rate_limit: Simulate rate limiting
        """
        super().__init__(fail_rate, slow_response)
        self.rate_limit = rate_limit
        self.rate_limit_counter = 0

    def get_data(
        self, latitude: float, longitude: float, start_year: int, end_year: int, parameters: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get mock NASA POWER climate data.

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_year: Start year
            end_year: End year
            parameters: List of parameter codes (None = all)

        Returns:
            DataFrame with date and climate variables

        Raises:
            MockAPIError: If configured to fail or rate limited
        """
        self.record_call()
        self.simulate_delay()

        # Check rate limiting
        if self.rate_limit:
            self.rate_limit_counter += 1
            if self.rate_limit_counter > 10:
                from .mock_base import MockAPIError

                raise MockAPIError("Rate limit exceeded", status_code=429)

        if self.simulate_failure():
            from .mock_base import MockAPIError

            raise MockAPIError("NASA POWER API request failed", status_code=500)

        # Default parameters
        if parameters is None:
            parameters = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "ALLSKY_SFC_SW_DWN"]

        # Validate parameters
        invalid = set(parameters) - set(self.AVAILABLE_PARAMETERS)
        if invalid:
            from .mock_base import MockAPIError

            raise MockAPIError(f"Invalid parameters: {invalid}", status_code=400)

        # Generate date range (daily data)
        dates = MockDataGenerator.create_date_range(start_year, end_year, freq="D")

        # Initialize DataFrame
        df = pd.DataFrame({"date": dates})

        # Generate each requested parameter
        for param in parameters:
            df[param] = self._generate_parameter_data(param, dates, latitude, longitude)

        # Add metadata
        df["latitude"] = latitude
        df["longitude"] = longitude
        df["source"] = "NASA_POWER"

        # Add some missing data (realistic)
        df = MockDataGenerator.apply_missing_data(df, missing_rate=0.005, columns=parameters)

        return df

    def _generate_parameter_data(
        self, parameter: str, dates: pd.DatetimeIndex, latitude: float, longitude: float
    ) -> np.ndarray:
        """
        Generate realistic data for a specific parameter.

        Args:
            parameter: Parameter code
            dates: Date range
            latitude: Latitude
            longitude: Longitude

        Returns:
            Array of parameter values
        """
        if parameter in ["T2M", "T2M_MAX", "T2M_MIN"]:
            return self._generate_temperature(parameter, dates, latitude)
        elif parameter == "RH2M":
            return self._generate_humidity(dates, latitude)
        elif parameter == "ALLSKY_SFC_SW_DWN":
            return self._generate_solar_radiation(dates, latitude)
        elif parameter == "WS2M":
            return self._generate_wind_speed(dates)
        elif parameter == "PRECTOTCORR":
            return self._generate_precipitation(dates)
        else:
            # Generic pattern for unknown parameters
            return np.random.normal(50, 10, len(dates))

    def _generate_temperature(self, param_type: str, dates: pd.DatetimeIndex, latitude: float) -> np.ndarray:
        """Generate realistic temperature data."""
        # Base seasonal pattern
        base_temp = MockDataGenerator.generate_seasonal_pattern(
            dates,
            base_value=self.BASE_TEMP,
            amplitude=self.TEMP_SEASONAL_AMP,
            peaks=[1, 10],  # Warm in Jan and Oct (southern hemisphere)
        )

        # Latitude adjustment (cooler at higher elevations/latitudes)
        lat_adjustment = (latitude + 6) * 0.3  # Tanzania centered at ~-6°
        base_temp = base_temp - lat_adjustment

        # Add daily variation
        daily_noise = MockDataGenerator.generate_autocorrelated_noise(len(dates), autocorr=0.8, std=1.5)
        temp = base_temp + daily_noise

        # Adjust for max/min
        if param_type == "T2M_MAX":
            temp = temp + np.random.uniform(3, 7, len(dates))
        elif param_type == "T2M_MIN":
            temp = temp - np.random.uniform(3, 7, len(dates))

        return temp

    def _generate_humidity(self, dates: pd.DatetimeIndex, latitude: float) -> np.ndarray:
        """Generate realistic humidity data."""
        # Inverse seasonal pattern (higher during rainy seasons)
        humidity = MockDataGenerator.generate_seasonal_pattern(
            dates,
            base_value=self.BASE_HUMIDITY,
            amplitude=self.HUMIDITY_SEASONAL_AMP,
            peaks=[4, 11],  # High during rain seasons
        )

        # Add noise
        humidity = MockDataGenerator.add_noise(humidity, noise_std=5.0)

        # Constrain to 0-100%
        return np.clip(humidity, 20, 98)

    def _generate_solar_radiation(self, dates: pd.DatetimeIndex, latitude: float) -> np.ndarray:
        """Generate realistic solar radiation data."""
        # Seasonal pattern (higher in dry season)
        solar = MockDataGenerator.generate_seasonal_pattern(
            dates, base_value=self.BASE_SOLAR, amplitude=self.SOLAR_SEASONAL_AMP, peaks=[7, 1]  # Peak in dry seasons
        )

        # Cloud cover variation (inverse of humidity pattern)
        months = dates.month
        cloud_factor = 1.0 - 0.15 * np.sin((months - 4) * np.pi / 6)
        solar = solar * cloud_factor

        # Add noise
        solar = MockDataGenerator.add_noise(solar, noise_std=1.5)

        return np.maximum(solar, 5.0)  # Minimum radiation

    def _generate_wind_speed(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """Generate realistic wind speed data."""
        base_wind = 3.0  # m/s average
        seasonal = MockDataGenerator.generate_seasonal_pattern(
            dates, base_value=base_wind, amplitude=1.5, peaks=[7, 8]  # Windier in dry season
        )

        # Add daily variation
        wind = MockDataGenerator.add_noise(seasonal, noise_std=0.8)

        return np.maximum(wind, 0.5)  # Minimum wind

    def _generate_precipitation(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """Generate precipitation (note: usually use CHIRPS instead)."""
        # Simple rainfall pattern (users should prefer CHIRPS)
        rainfall = MockDataGenerator.generate_seasonal_pattern(dates, base_value=2.0, amplitude=4.0, peaks=[4, 11])

        rainfall = MockDataGenerator.add_noise(rainfall, noise_std=1.0)
        return np.maximum(rainfall, 0)

    def get_http_response(
        self, latitude: float, longitude: float, start_date: str, end_date: str, parameters: str
    ) -> Dict:
        """
        Get mock HTTP API response in NASA POWER format.

        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)
            parameters: Comma-separated parameter codes

        Returns:
            Mock HTTP response dictionary
        """
        # Parse dates
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")

        # Parse parameters
        param_list = [p.strip() for p in parameters.split(",")]

        # Get data
        df = self.get_data(
            latitude=latitude, longitude=longitude, start_year=start.year, end_year=end.year, parameters=param_list
        )

        # Filter to date range
        df = df[(df["date"] >= start) & (df["date"] <= end)]

        # Build NASA POWER-like response
        data = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
            "properties": {"parameter": {}},
        }

        # Add each parameter's time series
        for param in param_list:
            data["properties"]["parameter"][param] = {
                df.loc[i, "date"].strftime("%Y%m%d"): df.loc[i, param]
                for i in df.index
                if not pd.isna(df.loc[i, param])
            }

        return MockResponseBuilder.build_json_response(data)


def get_mock_nasa_power(**kwargs) -> MockNASAPowerAPI:
    """
    Get a mock NASA POWER API instance.

    Args:
        **kwargs: Additional arguments for mock constructor

    Returns:
        Mock NASA POWER API instance
    """
    return MockNASAPowerAPI(**kwargs)
