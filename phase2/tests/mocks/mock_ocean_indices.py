"""
Mock Ocean Indices API - NOAA Climate Indices

Simulates NOAA ONI (ENSO) and IOD data from NOAA servers.
"""

import numpy as np
import pandas as pd

from .mock_base import BaseMockAPI, MockDataGenerator


class MockOceanIndicesAPI(BaseMockAPI):
    """
    Mock implementation of NOAA Ocean Indices API.

    Simulates ONI (Oceanic Niño Index) and IOD (Indian Ocean Dipole) data.
    """

    def __init__(self, fail_rate: float = 0.0, slow_response: bool = False):
        super().__init__(fail_rate, slow_response)

    def get_data(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Get mock ocean indices data.

        Args:
            start_year: Start year
            end_year: End year

        Returns:
            DataFrame with ONI and IOD values
        """
        self.record_call()
        self.simulate_delay()

        if self.simulate_failure():
            from .mock_base import MockAPIError

            raise MockAPIError("Ocean indices data retrieval failed", status_code=500)

        # Monthly data
        dates = MockDataGenerator.create_date_range(start_year, end_year, freq="MS")

        # Generate ONI (ENSO) pattern
        oni = self._generate_oni_pattern(dates)

        # Generate IOD pattern
        iod = self._generate_iod_pattern(dates)

        # Classify ENSO phase
        enso_phase = self._classify_enso(oni)

        df = pd.DataFrame({"date": dates, "oni": oni, "iod": iod, "enso_phase": enso_phase, "source": "NOAA"})

        return df

    def _generate_oni_pattern(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """
        Generate realistic ENSO ONI pattern.

        ONI oscillates between El Niño (+), La Niña (-), and Neutral
        with ~3-7 year cycle (ENSO periodicity).
        """
        months_since_start = np.arange(len(dates))

        # Primary ENSO cycle (~3.5 years average)
        cycle1 = np.sin(months_since_start * 2 * np.pi / 42)  # 3.5 year cycle

        # Secondary modulation (~5 years)
        cycle2 = 0.5 * np.sin(months_since_start * 2 * np.pi / 60)

        # Combine cycles
        oni = 1.2 * (cycle1 + cycle2)

        # Add noise
        oni = MockDataGenerator.add_noise(oni, noise_std=0.3)

        # Add some persistence (autocorrelation)
        noise_autocorr = MockDataGenerator.generate_autocorrelated_noise(len(dates), autocorr=0.7, std=0.2)
        oni = oni + noise_autocorr

        # Clip to realistic range
        return np.clip(oni, -2.5, 2.5)

    def _generate_iod_pattern(self, dates: pd.DatetimeIndex) -> np.ndarray:
        """
        Generate realistic IOD pattern.

        IOD has similar characteristics to ENSO but with different
        phase and smaller amplitude.
        """
        months_since_start = np.arange(len(dates))

        # IOD cycle (~2-5 years, slightly different from ENSO)
        cycle = np.sin(months_since_start * 2 * np.pi / 36)  # 3 year cycle

        # IOD is strongest in Sep-Nov
        seasonal_mod = 1.0 + 0.3 * np.sin((dates.month - 10) * 2 * np.pi / 12)

        iod = 0.8 * cycle * seasonal_mod

        # Add noise
        iod = MockDataGenerator.add_noise(iod, noise_std=0.2)

        # Clip to realistic range
        return np.clip(iod, -1.5, 1.5)

    def _classify_enso(self, oni: np.ndarray) -> np.ndarray:
        """
        Classify ENSO phase based on ONI value.

        Thresholds:
        - El Niño: ONI >= 0.5
        - La Niña: ONI <= -0.5
        - Neutral: -0.5 < ONI < 0.5
        """
        phases = np.where(oni >= 0.5, "El Niño", np.where(oni <= -0.5, "La Niña", "Neutral"))
        return phases

    def get_oni_data(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Get only ONI data."""
        df = self.get_data(start_year, end_year)
        return df[["date", "oni", "enso_phase"]]

    def get_iod_data(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Get only IOD data."""
        df = self.get_data(start_year, end_year)
        return df[["date", "iod"]]


def get_mock_ocean_indices(**kwargs) -> MockOceanIndicesAPI:
    """Get a mock Ocean Indices API instance."""
    return MockOceanIndicesAPI(**kwargs)
