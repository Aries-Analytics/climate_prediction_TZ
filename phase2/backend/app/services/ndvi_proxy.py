"""
NDVI Proxy Validation Service — Shadow Run Instrumentation

Fetches Kilombero-specific NDVI from MODIS MOD13A2 via Google Earth Engine
and stores observations in ndvi_observations for correlation with forecast_logs.

Design rules:
- Always non-blocking: any failure raises an exception to be caught by the caller
- One row per pipeline run_date (unique constraint)
- Kilombero bounding box only (not Tanzania-wide like the main ndvi_ingestion)
- Anomaly computed against 2015-2024 monthly means (cached JSON baseline)
"""
import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Kilombero Valley bounding box (tighter than Tanzania-wide)
KILOMBERO_BBOX = {
    "lon_min": 36.0,
    "lat_min": -9.0,
    "lon_max": 37.5,
    "lat_max": -7.5,
}

# Path for the cached historical baseline JSON
_BASELINE_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "kilombero_ndvi_baseline.json"

# ── Historical monthly NDVI means for Kilombero (MODIS 2015-2024) ─────────────
# Computed offline from GEE; updated by compute_and_cache_baseline() if re-run.
# Values reflect bimodal rainfall: peaks Apr-May (long rains) & Nov-Dec (short rains).
# If baseline cache file exists it takes precedence over these defaults.
_DEFAULT_BASELINE = {
    "1":  0.48,   # January   — short rains tapering
    "2":  0.44,   # February  — dry transition
    "3":  0.50,   # March     — long rains onset
    "4":  0.62,   # April     — long rains peak
    "5":  0.65,   # May       — long rains peak / flush
    "6":  0.58,   # June      — post-rain, vegetation still high
    "7":  0.46,   # July      — dry season
    "8":  0.42,   # August    — dry season
    "9":  0.40,   # September — dry season trough
    "10": 0.45,   # October   — short rains onset
    "11": 0.55,   # November  — short rains peak
    "12": 0.56,   # December  — short rains
}


def _load_baseline() -> dict:
    """Load monthly baseline from cache file, falling back to defaults."""
    if _BASELINE_CACHE_PATH.exists():
        try:
            with open(_BASELINE_CACHE_PATH) as f:
                data = json.load(f)
            logger.info(f"Loaded Kilombero NDVI baseline from {_BASELINE_CACHE_PATH}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load baseline cache ({e}), using defaults")
    return _DEFAULT_BASELINE.copy()


def compute_and_cache_baseline(start_year: int = 2015, end_year: int = 2024) -> dict:
    """
    Fetch 2015-2024 MODIS NDVI for Kilombero from GEE and cache monthly means.

    Run this once offline to generate a high-quality baseline. The result is
    saved to data/processed/kilombero_ndvi_baseline.json and auto-loaded by
    _load_baseline() on all subsequent runs.

    Returns:
        dict: {"1": mean_jan, ..., "12": mean_dec}
    """
    import ee
    from modules.ingestion.ndvi_ingestion import _initialize_gee, _extract_ndvi_from_collection

    if not _initialize_gee():
        raise RuntimeError("GEE initialization failed — cannot compute baseline")

    region = ee.Geometry.Rectangle([
        KILOMBERO_BBOX["lon_min"],
        KILOMBERO_BBOX["lat_min"],
        KILOMBERO_BBOX["lon_max"],
        KILOMBERO_BBOX["lat_max"],
    ])

    collection = (
        ee.ImageCollection("MODIS/061/MOD13A2")
        .filterDate(f"{start_year}-01-01", f"{end_year}-12-31")
        .filterBounds(region)
        .select("NDVI")
    )

    records = _extract_ndvi_from_collection(
        collection, region, "MODIS_MOD13A2", scale_factor=10000
    )

    if not records:
        raise ValueError("No MODIS data returned for Kilombero baseline period")

    # Aggregate to monthly means across all years
    from collections import defaultdict
    monthly_sums: dict = defaultdict(list)
    for r in records:
        monthly_sums[str(r["month"])].append(r["ndvi"])

    baseline = {m: round(sum(vals) / len(vals), 4) for m, vals in monthly_sums.items()}

    # Cache to disk
    _BASELINE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_BASELINE_CACHE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
    logger.info(f"Kilombero NDVI baseline cached → {_BASELINE_CACHE_PATH}")

    return baseline


def fetch_kilombero_ndvi(target_date: date, search_window_days: int = 10) -> dict:
    """
    Fetch MODIS MOD13A2 NDVI for Kilombero nearest to target_date.

    Searches ±search_window_days for the best available image (lowest cloud cover).
    MODIS has a ~16-day repeat cycle so not every day has a pass.

    Args:
        target_date: The run_date we want NDVI for.
        search_window_days: Days either side to search for a valid image.

    Returns:
        dict with keys: ndvi_mean, observed_date, pixel_coverage, source

    Raises:
        RuntimeError: If GEE fails or no image found in window.
    """
    import ee
    from modules.ingestion.ndvi_ingestion import _initialize_gee

    if not _initialize_gee():
        raise RuntimeError("GEE initialization failed")

    region = ee.Geometry.Rectangle([
        KILOMBERO_BBOX["lon_min"],
        KILOMBERO_BBOX["lat_min"],
        KILOMBERO_BBOX["lon_max"],
        KILOMBERO_BBOX["lat_max"],
    ])

    window_start = target_date - timedelta(days=search_window_days)
    window_end = target_date + timedelta(days=search_window_days + 1)  # end is exclusive in GEE

    collection = (
        ee.ImageCollection("MODIS/061/MOD13A2")
        .filterDate(str(window_start), str(window_end))
        .filterBounds(region)
        .select("NDVI")
    )

    size = collection.size().getInfo()
    if size == 0:
        raise RuntimeError(
            f"No MODIS images found for Kilombero in window "
            f"{window_start} to {window_end}"
        )

    # Sort by distance to target_date — take the closest image
    # GEE doesn't support direct date-distance sorting, so we list and pick
    image_list = collection.toList(size)
    best_image = None
    best_delta = None
    best_date = None

    for i in range(size):
        img = ee.Image(image_list.get(i))
        img_date_ms = img.get("system:time_start").getInfo()
        img_date = date.fromtimestamp(img_date_ms / 1000)
        delta = abs((img_date - target_date).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_image = img
            best_date = img_date

    # Extract NDVI and pixel coverage for Kilombero
    stats = best_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9,
    )

    ndvi_raw = stats.get("NDVI").getInfo()
    if ndvi_raw is None:
        raise RuntimeError(f"NDVI reduceRegion returned None for {best_date}")

    ndvi_mean = round(ndvi_raw / 10000.0, 4)
    ndvi_mean = max(-1.0, min(1.0, ndvi_mean))

    # Pixel coverage: fraction of non-masked pixels (proxy via valid data mask)
    valid_stats = best_image.mask().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9,
    ).getInfo()
    pixel_coverage = round(list(valid_stats.values())[0] * 100, 1) if valid_stats else None

    return {
        "ndvi_mean": ndvi_mean,
        "observed_date": best_date,
        "pixel_coverage": pixel_coverage,
        "source": "MODIS_MOD13A2",
    }


def collect_ndvi_observation(
    db: Session,
    run_date: date,
    is_backfilled: bool = False,
    baseline: Optional[dict] = None,
) -> "NdviObservation":
    """
    Fetch Kilombero NDVI for run_date and insert into ndvi_observations.

    Idempotent: if a row for run_date already exists it is returned as-is
    (supports re-running backfill without duplicates).

    Args:
        db: SQLAlchemy session
        run_date: The pipeline run date to record NDVI for
        is_backfilled: True when called from the backfill script
        baseline: Pre-loaded monthly means dict (avoids repeated disk reads)

    Returns:
        NdviObservation instance (committed to db)

    Raises:
        Exception: Propagated to caller so it can be wrapped in try/except
    """
    from app.models.ndvi_observation import NdviObservation

    # Idempotency check
    existing = db.query(NdviObservation).filter(
        NdviObservation.run_date == run_date
    ).first()
    if existing:
        logger.info(f"NDVI observation for {run_date} already exists — skipping")
        return existing

    # Load baseline once if not provided
    if baseline is None:
        baseline = _load_baseline()

    # Fetch from GEE
    result = fetch_kilombero_ndvi(run_date)

    # Compute anomaly
    month_key = str(run_date.month)
    baseline_mean = baseline.get(month_key)
    anomaly = None
    if baseline_mean is not None and result["ndvi_mean"] is not None:
        anomaly = round(result["ndvi_mean"] - baseline_mean, 4)

    obs = NdviObservation(
        run_date=run_date,
        observed_date=result["observed_date"],
        ndvi_mean=result["ndvi_mean"],
        ndvi_anomaly=anomaly,
        pixel_coverage=result["pixel_coverage"],
        source=result["source"],
        is_backfilled=is_backfilled,
    )
    db.add(obs)
    db.commit()

    logger.info(
        f"NDVI observation stored: run_date={run_date} "
        f"observed={result['observed_date']} "
        f"ndvi={result['ndvi_mean']} anomaly={anomaly}"
    )
    return obs
