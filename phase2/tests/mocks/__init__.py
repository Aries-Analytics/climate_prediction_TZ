"""
Mock API implementations for climate data integration testing.

This package provides mock versions of all external APIs used in the pipeline,
enabling fast, reliable testing without making actual network calls.
"""

from .mock_base import BaseMockAPI, MockDataGenerator, MockResponseBuilder, MockAPIError
from .mock_chirps import MockCHIRPSAPI, MockCHIRPSMultiLocation, get_mock_chirps
from .mock_nasa_power import MockNASAPowerAPI, get_mock_nasa_power
from .mock_era5 import MockERA5API, get_mock_era5
from .mock_ndvi import MockNDVIAPI, get_mock_ndvi
from .mock_ocean_indices import MockOceanIndicesAPI, get_mock_ocean_indices

__all__ = [
    # Base classes
    'BaseMockAPI',
    'MockDataGenerator',
    'MockResponseBuilder',
    'MockAPIError',
    # Mock implementations
    'MockCHIRPSAPI',
    'MockCHIRPSMultiLocation',
    'MockNASAPowerAPI',
    'MockERA5API',
    'MockNDVIAPI',
    'MockOceanIndicesAPI',
    # Factory functions
    'get_mock_chirps',
    'get_mock_nasa_power',
    'get_mock_era5',
    'get_mock_ndvi',
    'get_mock_ocean_indices',
]

