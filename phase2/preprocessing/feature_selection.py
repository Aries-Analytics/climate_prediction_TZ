"""
Feature Selection Module for Climate Prediction Model

This module provides methods to reduce feature dimensionality from 640 to 50-100 features
using correlation-based, model-based importance, and hybrid selection approaches.

Key objectives:
- Reduce overfitting risk by improving feature-to-sample ratio
- Maintain representation from all 5 data sources
- Remove redundant features (correlation > 0.95)
- Preserve model performance (validation R² within 5% of original)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
import xgboost as xgb
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class FeatureSelectionResult:
    """Container for feature selection results and metadata."""
    
    def __init__(
        self,
        selected_features: List[str],
        feature_scores: Dict[str, float],
        selection_method: str,
        original_count: int,
        selected_count: int,
        source_distribution: Dict[str, int],
        correlation_matrix: np.ndarray = None,
        timestamp: datetime = None
    ):
        self.selected_features = selected_features
        self.feature_scores = feature_scores
        self.selection_method = selection_method
        self.original_count = original_count
        self.selected_count = selected_count
        self.source_distribution = source_distribution
        self.correlation_matrix = correlation_matrix
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'selected_features': self.selected_features,
            'feature_scores': self.feature_scores,
            'selection_method': self.selection_method,
            'original_count': self.original_count,
            'selected_count': self.selected_count,
            'source_distribution': self.source_distribution,
            'timestamp': self.timestamp.isoformat()
        }
    
    def save(self, filepath: str):
        """Save feature selection results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Feature selection results saved to {filepath}")


def identify_feature_source(feature_name: str) -> str:
    """
    Identify which data source a feature belongs to.
    
    Maps feature names (including lag/rolling/interaction derivatives) back to
    their original data source. Uses prefix matching for robustness against
    derived feature name patterns like 'temp_2m_lag_6_lag_6'.
    
    Args:
        feature_name: Name of the feature
        
    Returns:
        Source name: 'CHIRPS', 'NASA_POWER', 'ERA5', 'NDVI', or 'Ocean_Indices'
    """
    feature_lower = feature_name.lower()
    
    # --- CHIRPS (rainfall, precipitation, drought/flood derived) ---
    chirps_keywords = [
        'chirps', 'precipitation', 'rainfall', 'precip',
        'flood_risk', 'drought', 'dry_day', 'is_dry_day',
        'consecutive_dry', 'cumulative_excess', 'spi',
        'wet_day', 'rain_anomal',
    ]
    if any(kw in feature_lower for kw in chirps_keywords):
        return 'CHIRPS'
    
    # --- NDVI (vegetation indices) ---
    ndvi_keywords = [
        'ndvi', 'vegetation', 'vci', 'crop_stress',
    ]
    if any(kw in feature_lower for kw in ndvi_keywords):
        return 'NDVI'
    
    # --- Ocean Indices (ENSO, IOD) ---
    ocean_keywords = [
        'nino', 'el_nino', 'la_nina', 'enso',
        'soi', 'dmi', 'iod', 'ocean',
        'is_el_nino', 'is_strong_el_nino', 'is_la_nina',
    ]
    if any(kw in feature_lower for kw in ocean_keywords):
        return 'Ocean_Indices'
    
    # --- ERA5 (atmospheric reanalysis: wind, pressure, dewpoint, humidity, temp_2m) ---
    era5_keywords = [
        'era5', 'wind', 'pressure', 'surface_pressure',
        'dewpoint', 'temp_2m', 'humidity', 'rel_humidity',
        'total_precip', 'boundary_layer',
    ]
    if any(kw in feature_lower for kw in era5_keywords):
        return 'ERA5'
    
    # --- NASA POWER (solar, temperature min/max/mean/range, PET, VPD) ---
    nasa_keywords = [
        'nasa', 'temperature', 'solar', 'solar_rad',
        'temp_min', 'temp_max', 'temp_mean', 'temp_range',
        'temp_variabil', 'pet_mm', 'vpd', 'cloud_cover',
    ]
    if any(kw in feature_lower for kw in nasa_keywords):
        return 'NASA_POWER'
    
    # Fallback — log for future improvement
    logger.debug(f"Could not classify feature source for: {feature_name}")
    return 'Unknown'


def remove_highly_correlated_features(
    X: pd.DataFrame,
    threshold: float = 0.95
) -> List[str]:
    """
    Remove features with correlation > threshold to reduce redundancy.
    
    Args:
        X: Feature matrix
        threshold: Correlation threshold (default 0.95)
        
    Returns:
        List of features to keep
    """
    logger.info(f"Removing features with correlation > {threshold}")
    
    # Calculate correlation matrix
    corr_matrix = X.corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    
    # Find features with correlation greater than threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    features_to_keep = [col for col in X.columns if col not in to_drop]
    
    logger.info(f"Removed {len(to_drop)} highly correlated features")
    logger.info(f"Kept {len(features_to_keep)} features")
    
    return features_to_keep


def select_features_correlation(
    X: pd.DataFrame,
    y: pd.Series,
    threshold: float = 0.1,
    max_features: int = 150
) -> Tuple[List[str], Dict[str, float]]:
    """
    Select features based on correlation with target variable.
    
    Args:
        X: Feature matrix
        y: Target variable
        threshold: Minimum absolute correlation (default 0.1)
        max_features: Maximum features to select (default 150)
        
    Returns:
        Tuple of (selected feature names, feature scores)
    """
    logger.info("Selecting features by correlation with target")
    
    # Calculate correlations
    correlations = {}
    for col in X.columns:
        corr = np.corrcoef(X[col].fillna(0), y)[0, 1]
        correlations[col] = abs(corr) if not np.isnan(corr) else 0.0
    
    # Sort by absolute correlation
    sorted_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
    
    # Filter by threshold and limit
    selected = [
        feat for feat, score in sorted_features 
        if score >= threshold
    ][:max_features]
    
    scores = {feat: correlations[feat] for feat in selected}
    
    logger.info(f"Selected {len(selected)} features by correlation (threshold={threshold})")
    
    return selected, scores


def select_features_importance(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    method: str = 'random_forest',
    n_features: int = 150
) -> Tuple[List[str], Dict[str, float]]:
    """
    Select features using model-based importance.
    
    Args:
        X: Feature matrix (numpy array)
        y: Target variable (numpy array)
        feature_names: List of feature names
        method: 'random_forest', 'xgboost', or 'lasso'
        n_features: Number of features to select
        
    Returns:
        Tuple of (selected feature names, feature importance scores)
    """
    logger.info(f"Selecting features using {method} importance")
    
    # Handle NaN values
    X_clean = np.nan_to_num(X, nan=0.0)
    
    if method == 'random_forest':
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_clean, y)
        importances = model.feature_importances_
        
    elif method == 'xgboost':
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_clean, y)
        importances = model.feature_importances_
        
    elif method == 'lasso':
        model = Lasso(alpha=0.01, random_state=42, max_iter=1000)
        model.fit(X_clean, y)
        importances = np.abs(model.coef_)
        
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Create feature importance dictionary
    feature_importance = dict(zip(feature_names, importances))
    
    # Sort and select top features
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    selected = [feat for feat, _ in sorted_features[:n_features]]
    scores = {feat: feature_importance[feat] for feat in selected}
    
    logger.info(f"Selected {len(selected)} features using {method}")
    
    return selected, scores


def ensure_source_diversity(
    selected_features: List[str],
    all_features: List[str],
    feature_scores: Dict[str, float],
    min_per_source: int = 5
) -> List[str]:
    """
    Ensure selected features include representation from all data sources.
    
    Args:
        selected_features: Currently selected features
        all_features: All available features
        feature_scores: Scores for all features
        min_per_source: Minimum features per source (default 5)
        
    Returns:
        Updated list of selected features with source diversity
    """
    logger.info("Ensuring source diversity in selected features")
    
    # Count features per source in current selection
    source_counts = {}
    for feat in selected_features:
        source = identify_feature_source(feat)
        source_counts[source] = source_counts.get(source, 0) + 1
    
    logger.info(f"Current source distribution: {source_counts}")
    
    # Identify underrepresented sources
    required_sources = ['CHIRPS', 'NASA_POWER', 'ERA5', 'NDVI', 'Ocean_Indices']
    features_to_add = []
    
    for source in required_sources:
        current_count = source_counts.get(source, 0)
        if current_count < min_per_source:
            needed = min_per_source - current_count
            logger.info(f"Source {source} needs {needed} more features")
            
            # Find top features from this source not yet selected
            source_features = [
                (feat, feature_scores.get(feat, 0.0))
                for feat in all_features
                if identify_feature_source(feat) == source and feat not in selected_features
            ]
            source_features.sort(key=lambda x: x[1], reverse=True)
            
            # Add top features from this source
            for feat, _ in source_features[:needed]:
                features_to_add.append(feat)
    
    updated_features = selected_features + features_to_add
    
    # Recount after additions
    final_counts = {}
    for feat in updated_features:
        source = identify_feature_source(feat)
        final_counts[source] = final_counts.get(source, 0) + 1
    
    logger.info(f"Final source distribution: {final_counts}")
    
    return updated_features


def select_features_hybrid(
    X: pd.DataFrame,
    y: pd.Series,
    target_features: int = 75,
    min_per_source: int = 5
) -> FeatureSelectionResult:
    """
    Combine multiple selection methods for robust feature set.
    
    Strategy:
    1. Remove features with correlation > 0.95 (redundancy)
    2. Select top 150 by correlation with target
    3. Select top 150 by Random Forest importance
    4. Select top 150 by XGBoost importance
    5. Take features appearing in top of at least 2 methods
    6. Ensure representation from all 5 data sources
    
    Args:
        X: Feature matrix (DataFrame)
        y: Target variable (Series)
        target_features: Target number of features (default 75)
        min_per_source: Minimum features per source (default 5)
        
    Returns:
        FeatureSelectionResult object
    """
    logger.info("=" * 60)
    logger.info("Starting hybrid feature selection")
    logger.info(f"Original features: {X.shape[1]}")
    logger.info(f"Target features: {target_features}")
    logger.info("=" * 60)
    
    original_count = X.shape[1]
    feature_names = list(X.columns)
    
    # Step 1: Remove highly correlated features
    features_after_corr = remove_highly_correlated_features(X, threshold=0.95)
    X_reduced = X[features_after_corr]
    logger.info(f"After correlation removal: {len(features_after_corr)} features")
    
    # Step 2: Correlation-based selection
    corr_features, corr_scores = select_features_correlation(
        X_reduced, y, threshold=0.05, max_features=150
    )
    
    # Step 3: Random Forest importance
    rf_features, rf_scores = select_features_importance(
        X_reduced.values, y.values, list(X_reduced.columns),
        method='random_forest', n_features=150
    )
    
    # Step 4: XGBoost importance
    xgb_features, xgb_scores = select_features_importance(
        X_reduced.values, y.values, list(X_reduced.columns),
        method='xgboost', n_features=150
    )
    
    # Step 5: Combine methods - features appearing in at least 2 methods
    feature_votes = {}
    all_scores = {}
    
    for feat in set(corr_features + rf_features + xgb_features):
        votes = 0
        total_score = 0.0
        
        if feat in corr_features:
            votes += 1
            total_score += corr_scores[feat]
        if feat in rf_features:
            votes += 1
            total_score += rf_scores[feat] * 10  # Scale RF scores
        if feat in xgb_features:
            votes += 1
            total_score += xgb_scores[feat] * 10  # Scale XGB scores
        
        feature_votes[feat] = votes
        all_scores[feat] = total_score / votes  # Average score
    
    # Select features with at least 2 votes, sorted by score
    candidate_features = [
        feat for feat, votes in feature_votes.items() if votes >= 2
    ]
    candidate_features.sort(key=lambda x: all_scores[x], reverse=True)
    
    # Take top target_features
    selected_features = candidate_features[:target_features]
    
    logger.info(f"After hybrid selection: {len(selected_features)} features")
    
    # Step 6: Ensure source diversity
    selected_features = ensure_source_diversity(
        selected_features,
        features_after_corr,
        all_scores,
        min_per_source=min_per_source
    )
    
    # Ensure all selected features have scores (add 0.0 for any missing)
    for feat in selected_features:
        if feat not in all_scores:
            all_scores[feat] = 0.0
    
    # Calculate final source distribution
    source_distribution = {}
    for feat in selected_features:
        source = identify_feature_source(feat)
        source_distribution[source] = source_distribution.get(source, 0) + 1
    
    logger.info("=" * 60)
    logger.info(f"Final selection: {len(selected_features)} features")
    logger.info(f"Source distribution: {source_distribution}")
    logger.info("=" * 60)
    
    # Create result object
    result = FeatureSelectionResult(
        selected_features=selected_features,
        feature_scores={feat: all_scores[feat] for feat in selected_features},
        selection_method='hybrid',
        original_count=original_count,
        selected_count=len(selected_features),
        source_distribution=source_distribution,
        correlation_matrix=X[selected_features].corr().values
    )
    
    return result


def apply_feature_selection(
    X: pd.DataFrame,
    selected_features: List[str]
) -> pd.DataFrame:
    """
    Apply feature selection to a dataset.
    
    Args:
        X: Feature matrix
        selected_features: List of features to keep
        
    Returns:
        Reduced feature matrix
    """
    missing_features = [f for f in selected_features if f not in X.columns]
    if missing_features:
        logger.warning(f"Missing {len(missing_features)} features in dataset: {missing_features[:5]}")
        # Filter to only features that exist in the dataset
        selected_features = [f for f in selected_features if f in X.columns]
        logger.info(f"Using {len(selected_features)} features that exist in dataset")
    
    if len(selected_features) == 0:
        raise ValueError("No selected features found in dataset!")
    
    return X[selected_features]
