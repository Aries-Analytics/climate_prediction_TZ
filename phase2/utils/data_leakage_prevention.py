"""
Data Leakage Prevention Utilities

This module provides functions to detect and remove features that may cause
data leakage by being derived from or highly correlated with the target variable.

Requirements: Prevent data leakage in ML pipelines
"""

import re
from typing import List, Set, Tuple
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger()


def detect_target_related_features(
    feature_names: List[str],
    target_name: str,
    strict: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Detect features that are likely derived from the target variable.
    
    THIS IS THE SINGLE SOURCE OF TRUTH FOR DATA LEAKAGE DETECTION.
    
    Args:
        feature_names: List of feature column names
        target_name: Name of the target variable (e.g., 'rainfall_mm')
        strict: If True, use strict matching. If False, allow some related features
        
    Returns:
        Tuple of (leaky_features, safe_features)
        
    Examples:
        >>> features = ['rainfall_mm_lag_1', 'temp_c', 'rainfall_14day']
        >>> leaky, safe = detect_target_related_features(features, 'rainfall_mm')
        >>> print(leaky)
        ['rainfall_mm_lag_1', 'rainfall_14day']
    """
    # Extract base name from target (e.g., 'rainfall' from 'rainfall_mm')
    target_base = target_name.split('_')[0].lower()
    
    # Alternative names for the same variable
    target_aliases = {
        'rainfall': ['rain', 'precip', 'precipitation', 'rainfall'],
        'temperature': ['temp', 'temperature'],
        'ndvi': ['ndvi', 'vegetation'],
    }
    
    # Get all possible names for this target
    possible_names = {target_base}
    for key, aliases in target_aliases.items():
        if target_base in aliases:
            possible_names.update(aliases)
    
    leaky_features = []
    safe_features = []
    
    # CRITICAL: Trigger features are ALWAYS derived from rainfall/climate data
    # These must be removed regardless of target variable
    trigger_patterns = [
        'drought_trigger', 'flood_trigger', 'crop_failure_trigger',
        'drought_severity', 'trigger_severity', 'any_trigger',
        'climate_drought_trigger', 'climate_flood_trigger',
        'moderate_stress_trigger', 'severe_stress_trigger',
        'trigger_confidence', 'days_since_trigger',
        'drought_stress_severity', 'any_climate_trigger'
    ]
    
    for feature in feature_names:
        feature_lower = feature.lower()
        is_leaky = False
        
        # Check if feature is a trigger (ALWAYS leaky for rainfall prediction)
        if any(pattern in feature_lower for pattern in trigger_patterns):
            is_leaky = True
            leaky_features.append(feature)
            continue
        
        # Check for interaction terms with target (e.g., oni_x_rainfall_mm)
        if '_x_' in feature_lower:
            for name in possible_names:
                if name in feature_lower:
                    is_leaky = True
                    break
        
        if is_leaky:
            leaky_features.append(feature)
            continue
        
        # Check if feature name contains target-related terms
        for name in possible_names:
            if name in feature_lower:
                # Check for specific patterns that indicate leakage
                leaky_patterns = [
                    f'{name}_lag_',      # Lagged versions of target
                    f'{name}_rolling',   # Rolling statistics of target
                    f'{name}_14day',     # Multi-day aggregations
                    f'{name}_7day',
                    f'{name}_30day',
                    f'{name}_90day',
                    f'{name}_180day',
                    f'{name}_clim',      # Climatology derived from target
                    f'extreme_{name}',   # Extreme events based on target
                    f'very_extreme_{name}',
                    f'heavy_{name}',     # Heavy rain events
                    f'{name}_event',
                    f'{name}_anomaly',   # Anomalies of target
                    f'excess_{name}',    # Excess rainfall/precip
                    f'prob_{name}',      # Probability features based on target
                    f'prob_normal_{name}',  # prob_normal_rainfall
                    f'prob_extreme_{name}',
                    f'prob_above_normal_{name}',  # prob_above_normal_rainfall
                    f'prob_below_normal_{name}',  # prob_below_normal_rainfall
                    f'favorable_{name}',  # favorable_rainfall_climate
                ]
                
                if any(pattern in feature_lower for pattern in leaky_patterns):
                    is_leaky = True
                    break
                
                # Check if feature starts with target name (e.g., 'precip_mm', 'rainfall_mm')
                if feature_lower.startswith(name + '_'):
                    is_leaky = True
                    break
                
                # Check for extreme event patterns
                if 'extreme' in feature_lower and 'rain' in feature_lower:
                    is_leaky = True
                    break
                
                # In strict mode, any feature with target name is suspicious
                if strict and name == feature_lower.split('_')[0]:
                    is_leaky = True
                    break
        
        if is_leaky:
            leaky_features.append(feature)
        else:
            safe_features.append(feature)
    
    if leaky_features:
        logger.warning(f"Detected {len(leaky_features)} potentially leaky features")
        for feat in leaky_features:
            logger.warning(f"  - {feat}")
    
    return leaky_features, safe_features


def detect_high_correlation_leakage(
    X: pd.DataFrame,
    y: pd.Series,
    threshold: float = 0.95
) -> List[str]:
    """
    Detect features with suspiciously high correlation with target.
    
    High correlation (>0.95) often indicates data leakage.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        threshold: Correlation threshold (default 0.95)
        
    Returns:
        List of feature names with high correlation
    """
    high_corr_features = []
    
    for col in X.columns:
        try:
            corr = abs(np.corrcoef(X[col].fillna(0), y.fillna(0))[0, 1])
            if corr > threshold:
                high_corr_features.append(col)
                logger.warning(f"Feature '{col}' has very high correlation with target: {corr:.4f}")
        except:
            continue
    
    return high_corr_features


def remove_leaky_features(
    X: pd.DataFrame,
    target_name: str,
    y: pd.Series = None,
    strict: bool = True,
    correlation_threshold: float = 0.95
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Remove features that may cause data leakage.
    
    Args:
        X: Feature DataFrame
        target_name: Name of target variable
        y: Target Series (optional, for correlation check)
        strict: Use strict name matching
        correlation_threshold: Threshold for correlation-based detection
        
    Returns:
        Tuple of (cleaned_X, removed_features, reason_for_removal)
    """
    logger.info(f"Checking for data leakage in {len(X.columns)} features")
    logger.info(f"Target variable: {target_name}")
    
    all_removed = []
    removal_reasons = []
    
    # 1. Name-based detection
    leaky_by_name, safe_by_name = detect_target_related_features(
        X.columns.tolist(),
        target_name,
        strict=strict
    )
    
    for feature in leaky_by_name:
        all_removed.append(feature)
        removal_reasons.append(f"{feature}: Name indicates derivation from target")
    
    # 2. Correlation-based detection (if y provided)
    if y is not None:
        X_safe = X[safe_by_name]
        high_corr = detect_high_correlation_leakage(X_safe, y, correlation_threshold)
        
        for feature in high_corr:
            if feature not in all_removed:
                all_removed.append(feature)
                removal_reasons.append(f"{feature}: Suspiciously high correlation with target")
    
    # Remove leaky features
    X_cleaned = X.drop(columns=all_removed, errors='ignore')
    
    logger.info(f"Removed {len(all_removed)} potentially leaky features")
    logger.info(f"Remaining features: {len(X_cleaned.columns)}")
    
    return X_cleaned, all_removed, removal_reasons


def validate_no_leakage(
    X: pd.DataFrame,
    y: pd.Series,
    target_name: str,
    max_correlation: float = 0.90
) -> bool:
    """
    Validate that no obvious data leakage exists.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        target_name: Name of target variable
        max_correlation: Maximum allowed correlation
        
    Returns:
        True if validation passes, False otherwise
    """
    logger.info("Validating for data leakage...")
    
    # Check for name-based leakage
    leaky_by_name, _ = detect_target_related_features(
        X.columns.tolist(),
        target_name,
        strict=True
    )
    
    if leaky_by_name:
        logger.error(f"VALIDATION FAILED: Found {len(leaky_by_name)} features with target-related names")
        return False
    
    # Check for correlation-based leakage
    high_corr = detect_high_correlation_leakage(X, y, max_correlation)
    
    if high_corr:
        logger.error(f"VALIDATION FAILED: Found {len(high_corr)} features with correlation > {max_correlation}")
        return False
    
    logger.info("✓ No obvious data leakage detected")
    return True
