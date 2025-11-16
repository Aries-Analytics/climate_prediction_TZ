"""
Feature Engineering Module - Phase 2

Creates cross-dataset features and composite insurance indicators from merged data.

CURRENT STATUS: Pass-through implementation
FUTURE: Will add interaction features, composite triggers, and domain-specific
        combinations after EDA with real data.

This module operates on the merged dataset (after all processing modules have run)
and will create features that require multiple data sources:
- Interaction features (ENSO × Rainfall, IOD × NDVI, etc.)
- Composite insurance triggers (combining multiple data sources)
- Overall risk scores (weighted combinations)
- Lag features (previous months)
- Temporal features (season, month indicators)
- Insurance payout calculators
- Domain-specific combinations
"""

import pandas as pd
from utils.config import get_output_path
from utils.logger import log_error, log_info


def build_features(merged_df):
    """
    Feature engineering pipeline for merged climate data.

    CURRENT: Pass-through implementation - returns processed features as-is.
    FUTURE: Will add cross-dataset interactions and composite indicators after
            analyzing real data and model performance.

    Parameters
    ----------
    merged_df : pd.DataFrame
        Merged dataset containing features from all processing modules
        (CHIRPS, NDVI, Ocean Indices, NASA POWER, ERA5)

    Returns
    -------
    pd.DataFrame
        Enhanced dataset with engineered features

    Notes
    -----
    The processing modules already create 148+ features including:
    - Drought/flood indicators (CHIRPS)
    - Vegetation health metrics (NDVI)
    - Climate forecasts (Ocean Indices)
    - Temperature features (NASA POWER)
    - Atmospheric indicators (ERA5)

    Additional feature engineering will be implemented after:
    1. Fetching real data
    2. Exploratory Data Analysis (EDA)
    3. Baseline model training
    4. Feature importance analysis

    Planned Features (for future implementation)
    --------------------------------------------
    - Interaction features:
      * ENSO × Rainfall (climate impact on precipitation)
      * IOD × NDVI (climate impact on vegetation)
      * Temperature × Rainfall (combined stress)
      * Rainfall × NDVI (vegetation response)

    - Composite insurance triggers:
      * Combined drought trigger (CHIRPS + NDVI + Ocean Indices)
      * Combined flood trigger (CHIRPS + Ocean Indices)
      * Multi-signal validation

    - Overall risk scores:
      * Weighted drought risk (35% CHIRPS, 40% NDVI, 25% Climate)
      * Weighted flood risk (70% CHIRPS, 30% Climate)
      * Overall climate risk (max of drought/flood)

    - Lag features:
      * Rainfall lags (1, 2, 3 months)
      * NDVI lags (1, 2 months)
      * ENSO/IOD lags (1, 2, 3 months)
      * Risk score lags

    - Temporal features:
      * Season indicators (short rains, long rains, dry)
      * Cyclical encoding (month_sin, month_cos)
      * Quarter indicators

    - Insurance payout calculators:
      * Drought payout (trigger × severity × confidence)
      * Flood payout (trigger × severity × confidence)
      * Crop failure payout
      * Tiered payout levels

    - Risk stratification:
      * Risk tiers (low, moderate, high, extreme)
      * Multi-hazard exposure
      * Premium rate suggestions

    - Domain-specific combinations:
      * Agricultural suitability index
      * Climate stress index
      * Vegetation response efficiency
      * Early warning composite
    """
    log_info("[FEATURE ENGINEERING] Processing merged dataset...")

    if merged_df is None or merged_df.empty:
        log_error("Input merged data is empty")
        raise ValueError("Cannot process empty merged data")

    df = merged_df.copy()

    # Log input statistics
    log_info(f"[FEATURE ENGINEERING] Input shape: {df.shape}")
    log_info(f"[FEATURE ENGINEERING] Input features: {len(df.columns)}")

    # CURRENT: Pass-through (no additional features yet)
    # The processing modules already created comprehensive features
    log_info("[FEATURE ENGINEERING] Using processed features as-is")
    log_info("[FEATURE ENGINEERING] Additional feature engineering will be implemented after EDA with real data")

    # Save output
    output_path = get_output_path("processed", "features_engineered.csv")
    df.to_csv(output_path, index=False)
    log_info(f"[FEATURE ENGINEERING] Output saved to: {output_path}")
    log_info(f"[FEATURE ENGINEERING] Output shape: {df.shape}")

    return df


# Placeholder for future implementation
def _add_interaction_features(df):
    """Add interaction features between data sources (future implementation)."""
    return df


def _add_composite_triggers(df):
    """Add composite insurance triggers (future implementation)."""
    return df


def _add_overall_risk_scores(df):
    """Add overall risk scores (future implementation)."""
    return df


def _add_lag_features(df):
    """Add lag features (future implementation)."""
    return df


def _add_temporal_features(df):
    """Add temporal features (future implementation)."""
    return df


def _add_insurance_payouts(df):
    """Add insurance payout calculators (future implementation)."""
    return df


def _add_risk_stratification(df):
    """Add risk stratification (future implementation)."""
    return df


def _add_domain_combinations(df):
    """Add domain-specific combinations (future implementation)."""
    return df
