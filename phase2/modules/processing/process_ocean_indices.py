"""
Ocean Indices Data Processing - Phase 3

Processes ENSO and IOD data with comprehensive climate impact indicators for East Africa.

Features created:
- ENSO/IOD strength classification and trends
- Seasonal rainfall forecasting indicators
- Combined climate impact scores
- Historical pattern matching for insurance risk
- Lead time indicators for early warning
- Drought and flood probability estimates
- Insurance-relevant climate triggers
"""

import numpy as np
import pandas as pd

from utils.config import get_output_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe


def process(data):
    """
    Process ocean climate indices with comprehensive impact indicators for insurance.
    
    Parameters
    ----------
    data : pd.DataFrame
        Raw ocean indices data with columns: year, month, oni, iod
    
    Returns
    -------
    pd.DataFrame
        Processed data with climate impact and insurance trigger features
    
    Features Added
    --------------
    - ENSO/IOD strength classification and trends
    - Combined climate impact scores
    - Seasonal rainfall probability forecasts
    - Drought and flood risk indicators
    - Historical pattern matching
    - Lead time indicators (3-6 month forecasts)
    - Insurance trigger thresholds
    - Climate phase transitions
    """
    log_info("[PROCESS] Processing Ocean Indices with climate impact and insurance indicators...")
    
    if data is None or data.empty:
        log_error("Input data is empty")
        raise ValueError("Cannot process empty Ocean Indices data")
    
    df = data.copy()
    
    # Ensure required columns exist
    required_cols = ['year', 'month']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Sort by date for time-series calculations
    df = df.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Create date column for easier manipulation
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    # 1. ENSO INDICATORS
    if 'oni' in df.columns:
        log_info("Processing ENSO indicators...")
        df = _add_enso_indicators(df)
    
    # 2. IOD INDICATORS
    if 'iod' in df.columns:
        log_info("Processing IOD indicators...")
        df = _add_iod_indicators(df)
    
    # 3. COMBINED CLIMATE IMPACTS
    if 'oni' in df.columns and 'iod' in df.columns:
        log_info("Calculating combined climate impacts...")
        df = _add_combined_climate_impacts(df)
    
    # 4. SEASONAL FORECASTING
    log_info("Generating seasonal forecasts...")
    df = _add_seasonal_forecasts(df)
    
    # 5. RAINFALL PROBABILITY ESTIMATES
    log_info("Calculating rainfall probabilities...")
    df = _add_rainfall_probabilities(df)
    
    # 6. DROUGHT AND FLOOD RISK
    log_info("Assessing drought and flood risk...")
    df = _add_climate_risk_indicators(df)
    
    # 7. INSURANCE TRIGGERS
    log_info("Calculating insurance triggers...")
    df = _add_insurance_triggers(df)
    
    # 8. QUALITY CHECKS
    df = _apply_quality_filters(df)
    
    # Drop temporary date column
    df = df.drop(columns=['date'])
    
    # Validate output
    expected_cols = ['year', 'month']
    if 'oni' in df.columns:
        expected_cols.extend(['enso_strength', 'enso_impact_score'])
    if 'iod' in df.columns:
        expected_cols.extend(['iod_strength', 'iod_impact_score'])
    
    validate_dataframe(df, expected_columns=expected_cols, dataset_name="Ocean Indices Processed")
    
    # Save processed data
    output_path = get_output_path("processed", "ocean_indices_processed.csv")
    df.to_csv(output_path, index=False)
    log_info(f"Processed Ocean Indices data saved to: {output_path}")
    log_info(f"[PROCESS] Ocean Indices processing complete. Output shape: {df.shape}")
    
    return df


def _add_enso_indicators(df):
    """
    Add comprehensive ENSO (El Niño-Southern Oscillation) indicators.
    
    ENSO is a major driver of climate variability in East Africa.
    """
    # ENSO strength classification
    df['enso_strength'] = pd.cut(
        df['oni'],
        bins=[-np.inf, -1.5, -0.5, 0.5, 1.5, np.inf],
        labels=['strong_la_nina', 'weak_la_nina', 'neutral', 'weak_el_nino', 'strong_el_nino']
    )
    
    # Numeric ENSO phase (-2 to 2)
    df['enso_phase'] = pd.cut(
        df['oni'],
        bins=[-np.inf, -1.5, -0.5, 0.5, 1.5, np.inf],
        labels=[-2, -1, 0, 1, 2]
    ).astype(int)
    
    # ENSO impact score for East Africa (-1 to 1, positive = more rain)
    df['enso_impact_score'] = np.clip(df['oni'] / 2, -1, 1)
    
    # ENSO trend (3-month change)
    df['enso_trend_3month'] = df['oni'].diff(3)
    
    # ENSO persistence (months in current phase)
    df['enso_persistence'] = _calculate_persistence(df['enso_phase'])
    
    # ENSO phase transition indicator
    df['enso_phase_change'] = (df['enso_phase'] != df['enso_phase'].shift(1)).astype(int)
    
    # El Niño indicator (ONI > 0.5 for insurance triggers)
    df['is_el_nino'] = (df['oni'] > 0.5).astype(int)
    
    # La Niña indicator (ONI < -0.5 for insurance triggers)
    df['is_la_nina'] = (df['oni'] < -0.5).astype(int)
    
    # Strong El Niño (historically associated with floods)
    df['is_strong_el_nino'] = (df['oni'] > 1.5).astype(int)
    
    # Strong La Niña (historically associated with droughts)
    df['is_strong_la_nina'] = (df['oni'] < -1.5).astype(int)
    
    # ENSO intensity (absolute value)
    df['enso_intensity'] = np.abs(df['oni'])
    
    return df


def _add_iod_indicators(df):
    """
    Add comprehensive IOD (Indian Ocean Dipole) indicators.
    
    IOD is particularly important for East African rainfall.
    """
    # IOD strength classification
    df['iod_strength'] = pd.cut(
        df['iod'],
        bins=[-np.inf, -0.8, -0.4, 0.4, 0.8, np.inf],
        labels=['strong_negative', 'weak_negative', 'neutral', 'weak_positive', 'strong_positive']
    )
    
    # Numeric IOD phase (-2 to 2)
    df['iod_phase'] = pd.cut(
        df['iod'],
        bins=[-np.inf, -0.8, -0.4, 0.4, 0.8, np.inf],
        labels=[-2, -1, 0, 1, 2]
    ).astype(int)
    
    # IOD impact score for East Africa (-1 to 1, positive = more rain)
    df['iod_impact_score'] = np.clip(df['iod'] / 1.5, -1, 1)
    
    # IOD trend (3-month change)
    df['iod_trend_3month'] = df['iod'].diff(3)
    
    # IOD persistence (months in current phase)
    df['iod_persistence'] = _calculate_persistence(df['iod_phase'])
    
    # IOD phase transition indicator
    df['iod_phase_change'] = (df['iod_phase'] != df['iod_phase'].shift(1)).astype(int)
    
    # Positive IOD indicator (IOD > 0.4 for insurance triggers)
    df['is_positive_iod'] = (df['iod'] > 0.4).astype(int)
    
    # Negative IOD indicator (IOD < -0.4 for insurance triggers)
    df['is_negative_iod'] = (df['iod'] < -0.4).astype(int)
    
    # Strong positive IOD (historically associated with floods)
    df['is_strong_positive_iod'] = (df['iod'] > 0.8).astype(int)
    
    # Strong negative IOD (historically associated with droughts)
    df['is_strong_negative_iod'] = (df['iod'] < -0.8).astype(int)
    
    # IOD intensity (absolute value)
    df['iod_intensity'] = np.abs(df['iod'])
    
    return df


def _add_combined_climate_impacts(df):
    """
    Add combined ENSO-IOD impact indicators.
    
    The interaction between ENSO and IOD is crucial for East African climate.
    """
    # Combined impact score (weighted average)
    # IOD has slightly stronger influence on East Africa
    df['combined_impact_score'] = (df['enso_impact_score'] * 0.4 + df['iod_impact_score'] * 0.6)
    
    # ENSO-IOD product (interaction term)
    df['enso_iod_product'] = df['oni'] * df['iod']
    
    # Favorable conditions for rainfall (El Niño + Positive IOD)
    df['favorable_rainfall_climate'] = (
        (df['oni'] > 0.5) & (df['iod'] > 0.4)
    ).astype(int)
    
    # Drought risk conditions (La Niña + Negative IOD)
    df['drought_risk_climate'] = (
        (df['oni'] < -0.5) & (df['iod'] < -0.4)
    ).astype(int)
    
    # Flood risk conditions (Strong El Niño + Strong Positive IOD)
    df['flood_risk_climate'] = (
        (df['oni'] > 1.0) & (df['iod'] > 0.6)
    ).astype(int)
    
    # Conflicting signals (ENSO and IOD in opposite phases)
    df['conflicting_signals'] = (
        ((df['oni'] > 0.5) & (df['iod'] < -0.4)) |
        ((df['oni'] < -0.5) & (df['iod'] > 0.4))
    ).astype(int)
    
    # Climate uncertainty score (0-1, higher = more uncertain)
    df['climate_uncertainty'] = _calculate_climate_uncertainty(df)
    
    # Combined intensity (maximum of ENSO and IOD intensity)
    df['combined_intensity'] = np.maximum(df['enso_intensity'], df['iod_intensity'])
    
    return df


def _add_seasonal_forecasts(df):
    """
    Add seasonal forecasting indicators.
    
    These provide lead time for insurance planning.
    """
    # Identify rainy seasons
    df['is_short_rains'] = df['month'].isin([10, 11, 12]).astype(int)  # Oct-Dec
    df['is_long_rains'] = df['month'].isin([3, 4, 5]).astype(int)      # Mar-May
    
    # Lead indicators (3-month ahead)
    if 'oni' in df.columns:
        df['enso_3month_ahead'] = df['oni'].shift(-3)
        df['enso_seasonal_impact'] = df['oni'] * df['is_short_rains']
    
    if 'iod' in df.columns:
        df['iod_3month_ahead'] = df['iod'].shift(-3)
        df['iod_seasonal_impact'] = df['iod'] * df['is_short_rains']
    
    # Forecast confidence (based on persistence and intensity)
    if 'oni' in df.columns and 'iod' in df.columns:
        df['forecast_confidence'] = _calculate_forecast_confidence(df)
    
    # Season-specific impact scores
    if 'combined_impact_score' in df.columns:
        df['short_rains_forecast'] = df['combined_impact_score'] * df['is_short_rains']
        df['long_rains_forecast'] = df['combined_impact_score'] * df['is_long_rains']
    
    return df


def _add_rainfall_probabilities(df):
    """
    Add rainfall probability estimates based on climate indices.
    
    These are empirical probabilities for insurance risk assessment.
    """
    # Initialize probability columns
    df['prob_above_normal_rainfall'] = 0.33  # Default (climatological)
    df['prob_below_normal_rainfall'] = 0.33
    df['prob_normal_rainfall'] = 0.34
    
    if 'oni' in df.columns and 'iod' in df.columns:
        # El Niño + Positive IOD: High probability of above-normal rainfall
        favorable = (df['oni'] > 0.5) & (df['iod'] > 0.4)
        df.loc[favorable, 'prob_above_normal_rainfall'] = 0.65
        df.loc[favorable, 'prob_below_normal_rainfall'] = 0.15
        df.loc[favorable, 'prob_normal_rainfall'] = 0.20
        
        # La Niña + Negative IOD: High probability of below-normal rainfall
        unfavorable = (df['oni'] < -0.5) & (df['iod'] < -0.4)
        df.loc[unfavorable, 'prob_above_normal_rainfall'] = 0.15
        df.loc[unfavorable, 'prob_below_normal_rainfall'] = 0.65
        df.loc[unfavorable, 'prob_normal_rainfall'] = 0.20
        
        # Strong El Niño: Very high probability of above-normal rainfall
        strong_el_nino = df['oni'] > 1.5
        df.loc[strong_el_nino, 'prob_above_normal_rainfall'] = 0.75
        df.loc[strong_el_nino, 'prob_below_normal_rainfall'] = 0.10
        df.loc[strong_el_nino, 'prob_normal_rainfall'] = 0.15
        
        # Strong La Niña: Very high probability of below-normal rainfall
        strong_la_nina = df['oni'] < -1.5
        df.loc[strong_la_nina, 'prob_above_normal_rainfall'] = 0.10
        df.loc[strong_la_nina, 'prob_below_normal_rainfall'] = 0.75
        df.loc[strong_la_nina, 'prob_normal_rainfall'] = 0.15
    
    # Drought probability (below-normal rainfall)
    df['drought_probability'] = df['prob_below_normal_rainfall']
    
    # Flood probability (above-normal rainfall, especially if extreme)
    df['flood_probability'] = df['prob_above_normal_rainfall'] * 0.5  # Not all above-normal = flood
    
    return df


def _add_climate_risk_indicators(df):
    """
    Add comprehensive climate risk indicators for insurance.
    """
    # Drought risk score (0-100)
    df['drought_risk_score'] = _calculate_drought_risk_score(df)
    
    # Flood risk score (0-100)
    df['flood_risk_score'] = _calculate_flood_risk_score(df)
    
    # Overall climate risk (maximum of drought and flood risk)
    df['overall_climate_risk'] = np.maximum(df['drought_risk_score'], df['flood_risk_score'])
    
    # Risk classification
    df['climate_risk_class'] = pd.cut(
        df['overall_climate_risk'],
        bins=[0, 25, 50, 75, 100],
        labels=['low', 'moderate', 'high', 'extreme']
    )
    
    # Early warning indicator (risk developing in next 3 months)
    if 'enso_3month_ahead' in df.columns and 'iod_3month_ahead' in df.columns:
        df['early_warning_drought'] = (
            (df['enso_3month_ahead'] < -0.5) & (df['iod_3month_ahead'] < -0.4)
        ).astype(int)
        
        df['early_warning_flood'] = (
            (df['enso_3month_ahead'] > 1.0) & (df['iod_3month_ahead'] > 0.6)
        ).astype(int)
    
    return df


def _add_insurance_triggers(df):
    """
    Add insurance trigger indicators based on climate indices.
    
    These are the key features for parametric climate insurance.
    """
    # DROUGHT TRIGGER (climate-based)
    # Trigger if: La Niña + Negative IOD persisting for 3+ months
    if 'oni' in df.columns and 'iod' in df.columns:
        df['climate_drought_trigger'] = (
            (df['oni'] < -0.5) &
            (df['iod'] < -0.4) &
            (df['enso_persistence'] >= 3)
        ).astype(int)
        
        # Drought trigger confidence
        drought_signals = [
            (df['oni'] < -0.5).astype(float),
            (df['iod'] < -0.4).astype(float),
            (df['enso_persistence'] >= 3).astype(float),
            (df['drought_probability'] > 0.5).astype(float)
        ]
        df['climate_drought_trigger_confidence'] = np.mean(drought_signals, axis=0)
    
    # FLOOD TRIGGER (climate-based)
    # Trigger if: Strong El Niño + Positive IOD
    if 'oni' in df.columns and 'iod' in df.columns:
        df['climate_flood_trigger'] = (
            (df['oni'] > 1.0) &
            (df['iod'] > 0.6)
        ).astype(int)
        
        # Flood trigger confidence
        flood_signals = [
            (df['oni'] > 1.0).astype(float),
            (df['iod'] > 0.6).astype(float),
            (df['flood_probability'] > 0.4).astype(float),
            (df['combined_intensity'] > 1.0).astype(float)
        ]
        df['climate_flood_trigger_confidence'] = np.mean(flood_signals, axis=0)
    
    # COMBINED TRIGGER
    if 'climate_drought_trigger' in df.columns and 'climate_flood_trigger' in df.columns:
        df['any_climate_trigger'] = (
            df['climate_drought_trigger'] | df['climate_flood_trigger']
        ).astype(int)
    
    # Trigger severity (for payout calculation)
    if 'drought_risk_score' in df.columns and 'flood_risk_score' in df.columns:
        df['trigger_severity'] = np.maximum(
            df['drought_risk_score'] / 100,
            df['flood_risk_score'] / 100
        )
    
    return df


def _calculate_persistence(phase_series):
    """
    Calculate how many consecutive months a climate phase has persisted.
    """
    persistence = pd.Series(0, index=phase_series.index)
    current_count = 0
    current_phase = None
    
    for i in range(len(phase_series)):
        if phase_series.iloc[i] == current_phase:
            current_count += 1
        else:
            current_phase = phase_series.iloc[i]
            current_count = 1
        persistence.iloc[i] = current_count
    
    return persistence


def _calculate_climate_uncertainty(df):
    """
    Calculate climate uncertainty score (0-1).
    
    Higher uncertainty when signals are weak or conflicting.
    """
    uncertainty = pd.Series(0.5, index=df.index)  # Default moderate uncertainty
    
    # Low uncertainty: Strong, consistent signals
    strong_consistent = (
        (df['enso_intensity'] > 1.0) &
        (df['iod_intensity'] > 0.6) &
        (df['conflicting_signals'] == 0)
    )
    uncertainty[strong_consistent] = 0.2
    
    # High uncertainty: Weak or conflicting signals
    weak_or_conflicting = (
        (df['enso_intensity'] < 0.5) |
        (df['iod_intensity'] < 0.3) |
        (df['conflicting_signals'] == 1)
    )
    uncertainty[weak_or_conflicting] = 0.8
    
    return uncertainty


def _calculate_forecast_confidence(df):
    """
    Calculate forecast confidence (0-1).
    
    Higher confidence when climate signals are strong and persistent.
    """
    confidence = pd.Series(0.5, index=df.index)  # Default moderate confidence
    
    # High confidence: Strong, persistent signals
    high_conf = (
        (df['combined_intensity'] > 1.0) &
        ((df['enso_persistence'] >= 3) | (df['iod_persistence'] >= 3)) &
        (df['conflicting_signals'] == 0)
    )
    confidence[high_conf] = 0.85
    
    # Low confidence: Weak, changing signals
    low_conf = (
        (df['combined_intensity'] < 0.5) |
        ((df['enso_phase_change'] == 1) | (df['iod_phase_change'] == 1))
    )
    confidence[low_conf] = 0.3
    
    return confidence


def _calculate_drought_risk_score(df):
    """
    Calculate drought risk score (0-100) based on climate indices.
    """
    score = pd.Series(0.0, index=df.index)
    
    if 'oni' in df.columns:
        # La Niña contribution (0-40 points)
        score += np.maximum(0, np.minimum(40, -df['oni'] * 20))
    
    if 'iod' in df.columns:
        # Negative IOD contribution (0-40 points)
        score += np.maximum(0, np.minimum(40, -df['iod'] * 25))
    
    if 'enso_persistence' in df.columns:
        # Persistence contribution (0-20 points)
        score += np.minimum(20, df['enso_persistence'] * 4)
    
    # Clip to 0-100
    score = np.clip(score, 0, 100)
    
    return score


def _calculate_flood_risk_score(df):
    """
    Calculate flood risk score (0-100) based on climate indices.
    """
    score = pd.Series(0.0, index=df.index)
    
    if 'oni' in df.columns:
        # El Niño contribution (0-40 points)
        score += np.maximum(0, np.minimum(40, df['oni'] * 20))
    
    if 'iod' in df.columns:
        # Positive IOD contribution (0-40 points)
        score += np.maximum(0, np.minimum(40, df['iod'] * 25))
    
    if 'enso_persistence' in df.columns:
        # Persistence contribution (0-20 points)
        score += np.minimum(20, df['enso_persistence'] * 4)
    
    # Clip to 0-100
    score = np.clip(score, 0, 100)
    
    return score


def _apply_quality_filters(df):
    """
    Apply quality filters to remove invalid data.
    """
    initial_count = len(df)
    
    # Remove unrealistic ONI values (typically -3 to 3)
    if 'oni' in df.columns:
        df = df[(df['oni'] >= -4) & (df['oni'] <= 4)]
    
    # Remove unrealistic IOD values (typically -2 to 2)
    if 'iod' in df.columns:
        df = df[(df['iod'] >= -3) & (df['iod'] <= 3)]
    
    # Log if significant data was removed
    removed_count = initial_count - len(df)
    if removed_count > 0:
        log_info(f"Quality filter removed {removed_count} invalid records ({removed_count/initial_count*100:.1f}%)")
    
    return df
