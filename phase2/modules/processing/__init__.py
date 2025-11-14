"""
Processing modules for climate data transformation and validation.

This package contains modules for processing raw climate data from various sources:
- NASA POWER
- ERA5
- CHIRPS
- NDVI
- Ocean Indices

Each processing module implements a process() function that:
1. Accepts raw data from ingestion
2. Validates and transforms the data
3. Saves processed output to outputs/processed/
4. Returns the processed DataFrame
"""

from . import (
    merge_processed,
    process_chirps,
    process_era5,
    process_nasa_power,
    process_ndvi,
    process_ocean_indices,
)

__all__ = [
    "merge_processed",
    "process_chirps",
    "process_era5",
    "process_nasa_power",
    "process_ndvi",
    "process_ocean_indices",
]
