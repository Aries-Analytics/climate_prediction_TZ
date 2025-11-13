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
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env (if present)
load_dotenv()

# ---------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]   # points to the phase2 folder
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
NASA_API_URL = os.getenv(
    "NASA_API_URL",
    "https://power.larc.nasa.gov/api/temporal/monthly/point"
)

ERA5_API_KEY = os.getenv("ERA5_API_KEY", None)

CHIRPS_BASE_URL = os.getenv(
    "CHIRPS_BASE_URL",
    "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
)

# NDVI source placeholder (empty by default; configure if/when needed)
NDVI_SOURCE = os.getenv("NDVI_SOURCE", "")

# Oceanic / atmospheric indices source (ENSO, IOD, etc.)
OCEAN_INDICES_SOURCE = os.getenv(
    "OCEAN_INDICES_SOURCE",
    "https://psl.noaa.gov/data/climateindices/list/"
)

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
    Example: get_data_path('raw', 'nasa_power.csv')
    """
    path = DATA_DIR.joinpath(*subpaths)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def get_output_path(*subpaths) -> Path:
    """
    Return a full Path inside the outputs directory.
    Example: get_output_path('processed', 'nasa_power_processed.csv')
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
    Ensure critical directories exist and warn if core env keys are missing.
    Call this at the start of a pipeline run.
    """
    # ensure directories
    for p in (DATA_DIR, DATA_DIR / "raw", DATA_DIR / "processed", DATA_DIR / "external",
              OUTPUT_DIR, OUTPUT_DIR / "processed"):
        p.mkdir(parents=True, exist_ok=True)
        print(f"[CONFIG] Verified directory: {p}")

    # warn about missing env keys that are likely needed for real ingestion
    if not NASA_API_URL:
        print("[WARN] NASA_API_URL is not set.")
    if not CHIRPS_BASE_URL:
        print("[WARN] CHIRPS_BASE_URL is not set.")
    # NDVI_SOURCE is optional (may be configured later)
