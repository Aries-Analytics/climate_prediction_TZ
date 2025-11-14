"""
utils/config.py

Centralized configuration for Phase 2 - Tanzania Climate Prediction.

Provides:
- base path constants (DATA_DIR, OUTPUT_DIR)
- data-source endpoint placeholders for the five chosen datasets
- path helpers (get_data_path, get_output_path)
- save helper (save_processed_output)
- a small environment validator (validate_environment)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env (if present)
load_dotenv()

# ---------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # points to the phase2 folder
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure core directories exist
(DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "external").mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "processed").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Data source endpoints / keys (placeholders or loaded from env)
# Only the five sources used in Phase 2 are included.
# ---------------------------------------------------------------------
NASA_API_URL = os.getenv("NASA_API_URL", "https://power.larc.nasa.gov/api/temporal/monthly/point")

ERA5_API_KEY = os.getenv("ERA5_API_KEY", None)

CHIRPS_BASE_URL = os.getenv("CHIRPS_BASE_URL", "https://data.chc.ucsb.edu/products/CHIRPS-2.0")

# NDVI source placeholder (empty by default; configure if/when needed)
NDVI_SOURCE = os.getenv("NDVI_SOURCE", "")

# Oceanic / atmospheric indices source (ENSO, IOD, etc.)
OCEAN_INDICES_SOURCE = os.getenv("OCEAN_INDICES_SOURCE", "https://psl.noaa.gov/data/climateindices/list/")

# ---------------------------------------------------------------------
# Project-wide constants
# ---------------------------------------------------------------------
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "Tanzania")
DEFAULT_CRS = os.getenv("DEFAULT_CRS", "EPSG:4326")


# ---------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------
def get_data_path(*subpaths) -> Path:
    """
    Return a full Path inside the data directory.

    Constructs absolute path to files in the data/ directory and creates parent
    directories if they don't exist.

    Parameters
    ----------
    *subpaths : str
        Variable number of path components to join (e.g., 'raw', 'nasa_power.csv').

    Returns
    -------
    pathlib.Path
        Absolute path to the specified location in data/ directory.

    Notes
    -----
    - Automatically creates parent directories if they don't exist
    - Returns Path object (not string) for better path manipulation
    - Base directory is phase2/data/

    Examples
    --------
    >>> from utils.config import get_data_path
    >>>
    >>> # Get path to raw NASA POWER data
    >>> path = get_data_path('raw', 'nasa_power.csv')
    >>> # Returns: /path/to/phase2/data/raw/nasa_power.csv
    >>>
    >>> # Get path to processed data directory
    >>> path = get_data_path('processed')
    >>> # Returns: /path/to/phase2/data/processed/
    """
    path = DATA_DIR.joinpath(*subpaths)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(*subpaths) -> Path:
    """
    Return a full Path inside the outputs directory.

    Constructs absolute path to files in the outputs/ directory and creates parent
    directories if they don't exist.

    Parameters
    ----------
    *subpaths : str
        Variable number of path components to join (e.g., 'processed', 'nasa_power_processed.csv').

    Returns
    -------
    pathlib.Path
        Absolute path to the specified location in outputs/ directory.

    Notes
    -----
    - Automatically creates parent directories if they don't exist
    - Returns Path object (not string) for better path manipulation
    - Base directory is phase2/outputs/

    Examples
    --------
    >>> from utils.config import get_output_path
    >>>
    >>> # Get path for processed output
    >>> path = get_output_path('processed', 'nasa_power_processed.csv')
    >>> # Returns: /path/to/phase2/outputs/processed/nasa_power_processed.csv
    >>>
    >>> # Get path to processed directory
    >>> path = get_output_path('processed')
    >>> # Returns: /path/to/phase2/outputs/processed/
    """
    path = OUTPUT_DIR.joinpath(*subpaths)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------
def save_processed_output(df, filename: str):
    """
    Save a pandas DataFrame into outputs/processed and return the file path.
    This is a small convenience wrapper used by processing modules.
    """
    try:
        out_path = get_output_path("processed", filename)
        # Use DataFrame.to_csv if possible, otherwise raise informative error
        if hasattr(df, "to_csv"):
            df.to_csv(out_path, index=False)
            print(f"[SAVE] Processed output saved to {out_path}")
            return out_path
        else:
            raise TypeError("save_processed_output expects a pandas DataFrame (or object with to_csv).")
    except Exception as e:
        # Keep the message simple for dry-run; processing modules/logging will capture details
        print(f"[ERROR] Failed to save processed output '{filename}': {e}")
        raise


# ---------------------------------------------------------------------
# Environment validation
# ---------------------------------------------------------------------
def validate_environment():
    """
    Validate environment setup and ensure required directories exist.

    Checks that all critical directories are present and warns about missing
    environment variables. Should be called at the start of pipeline execution.

    Notes
    -----
    **Directories Created:**

    - data/
    - data/raw/
    - data/processed/
    - data/external/
    - outputs/
    - outputs/processed/

    **Environment Variables Checked:**

    - NASA_API_URL: NASA POWER API endpoint
    - CHIRPS_BASE_URL: CHIRPS data portal URL
    - ERA5_API_KEY: Not checked (optional, only needed for ERA5)

    **Logging:**

    - Logs verification message for each directory created
    - Logs warnings for missing environment variables

    Examples
    --------
    >>> from utils.config import validate_environment
    >>>
    >>> # Validate environment at pipeline start
    >>> validate_environment()
    [CONFIG] Verified directory: /path/to/phase2/data
    [CONFIG] Verified directory: /path/to/phase2/data/raw
    ...
    """
    # ensure directories
    for p in (
        DATA_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        DATA_DIR / "external",
        OUTPUT_DIR,
        OUTPUT_DIR / "processed",
    ):
        p.mkdir(parents=True, exist_ok=True)
        print(f"[CONFIG] Verified directory: {p}")

    # warn about missing env keys that are likely needed for real ingestion
    if not NASA_API_URL:
        print("[WARN] NASA_API_URL is not set.")
    if not CHIRPS_BASE_URL:
        print("[WARN] CHIRPS_BASE_URL is not set.")
    # NDVI_SOURCE is optional (may be configured later)
