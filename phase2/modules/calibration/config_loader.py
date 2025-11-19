"""
Configuration loader for insurance trigger thresholds.

This module handles loading, validating, and providing access to trigger
threshold configurations stored in YAML format.

Functions:
- load_trigger_config: Load and validate trigger configuration from YAML
- validate_trigger_config: Validate configuration structure and values
- _get_default_config: Provide scientifically-justified default thresholds

Requirements: 7.2, 7.3
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, ValidationError, field_validator

from utils.logger import log_error, log_info, log_warning

# ============================================================================
# Pydantic Models for Configuration Validation
# ============================================================================


class ThresholdConfig(BaseModel):
    """Base model for threshold configuration with metadata."""

    threshold: Optional[float] = None
    rationale: str
    data_source: Optional[str] = None
    calibration_date: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional fields


class FloodTriggerConfig(BaseModel):
    """Flood trigger threshold configuration."""

    daily_rainfall_mm: Dict[str, Any]
    rainfall_7day_mm: Dict[str, Any]
    heavy_rain_days_7day: Dict[str, Any]
    rainfall_percentile: Dict[str, Any]

    @field_validator("daily_rainfall_mm")
    @classmethod
    def validate_daily_rainfall_threshold(cls, v):
        if v.get("threshold") is not None:
            threshold = v["threshold"]
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1000:
                raise ValueError(f"Daily rainfall threshold must be between 0 and 1000mm, got {threshold}")
        return v

    @field_validator("rainfall_7day_mm")
    @classmethod
    def validate_7day_rainfall_threshold(cls, v):
        if v.get("threshold") is not None:
            threshold = v["threshold"]
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 5000:
                raise ValueError(f"7-day rainfall threshold must be between 0 and 5000mm, got {threshold}")
        return v


class DroughtTriggerConfig(BaseModel):
    """Drought trigger threshold configuration."""

    spi_30day: Dict[str, Any]
    consecutive_dry_days: Dict[str, Any]
    rainfall_deficit_pct: Dict[str, Any]

    @field_validator("spi_30day")
    @classmethod
    def validate_spi_threshold(cls, v):
        if v.get("threshold") is not None:
            threshold = v["threshold"]
            if not isinstance(threshold, (int, float)) or threshold < -5 or threshold > 0:
                raise ValueError(f"SPI threshold must be between -5 and 0, got {threshold}")
        return v


class CropFailureTriggerConfig(BaseModel):
    """Crop failure trigger threshold configuration."""

    vci_threshold: Dict[str, Any]
    ndvi_anomaly_std: Dict[str, Any]
    crop_failure_risk_score: Dict[str, Any]

    @field_validator("vci_threshold")
    @classmethod
    def validate_vci_threshold(cls, v):
        if v.get("critical") is not None:
            critical = v["critical"]
            if not isinstance(critical, (int, float)) or critical < 0 or critical > 100:
                raise ValueError(f"VCI threshold must be between 0 and 100, got {critical}")
        return v


class TriggerThresholdsConfig(BaseModel):
    """Complete trigger threshold configuration."""

    version: str
    calibration_date: str
    data_period: str
    target_trigger_rates: Dict[str, float]
    flood_triggers: FloodTriggerConfig
    drought_triggers: DroughtTriggerConfig
    crop_failure_triggers: CropFailureTriggerConfig
    regional_adjustments: Optional[Dict[str, Any]] = None

    @field_validator("target_trigger_rates")
    @classmethod
    def validate_target_rates(cls, v):
        for trigger_type, rate in v.items():
            if not isinstance(rate, (int, float)) or rate <= 0 or rate >= 1:
                raise ValueError(f"Target rate for {trigger_type} must be between 0 and 1, got {rate}")
        return v

    class Config:
        extra = "allow"  # Allow additional fields


# ============================================================================
# Configuration Loading Functions
# ============================================================================


def load_trigger_config(config_path: Optional[str] = None) -> Dict:
    """
    Load trigger threshold configuration from YAML file with pydantic validation.

    This function loads the trigger configuration from a YAML file, validates it
    using pydantic models, and returns the configuration dictionary. If the file
    is missing or invalid, it falls back to scientifically-justified defaults
    with appropriate logging.

    Parameters
    ----------
    config_path : Optional[str]
        Path to configuration file. If None, uses default location
        'configs/trigger_thresholds.yaml'

    Returns
    -------
    Dict
        Dictionary containing validated trigger threshold configuration with keys:
        - version: Configuration version string
        - calibration_date: Date when thresholds were calibrated
        - data_period: Historical data period used for calibration
        - target_trigger_rates: Target activation rates for each trigger type
        - flood_triggers: Flood trigger threshold configuration
        - drought_triggers: Drought trigger threshold configuration
        - crop_failure_triggers: Crop failure trigger threshold configuration
        - regional_adjustments: Optional regional threshold adjustments

    Examples
    --------
    >>> config = load_trigger_config()
    >>> print(f"Flood threshold: {config['flood_triggers']['daily_rainfall_mm']['threshold']}mm")

    >>> config = load_trigger_config('custom_config.yaml')
    >>> print(f"Version: {config['version']}")

    Notes
    -----
    - If configuration file is missing, returns default configuration with logging
    - If configuration is invalid, returns default configuration with error logging
    - All validation errors are logged for debugging
    - Default configuration is based on WMO and FAO standards

    Requirements: 7.2, 7.3
    """
    if config_path is None:
        # Default configuration path
        config_path = os.path.join("configs", "trigger_thresholds.yaml")

    config_file = Path(config_path)

    # Check if configuration file exists
    if not config_file.exists():
        log_warning(f"Configuration file not found: {config_path}")
        log_warning("Using scientifically-justified default trigger thresholds")
        return _get_default_config()

    try:
        # Load YAML file
        log_info(f"Loading trigger configuration from: {config_path}")
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            log_error(f"Configuration file is empty: {config_path}")
            log_warning("Using default trigger thresholds")
            return _get_default_config()

        # Validate configuration structure and values
        is_valid, errors = validate_trigger_config(config)

        if not is_valid:
            log_error(f"Invalid configuration file: {config_path}")
            log_error("Configuration validation errors:")
            for error in errors:
                log_error(f"  - {error}")
            log_warning("Falling back to default trigger thresholds")
            return _get_default_config()

        # Configuration is valid
        log_info("✓ Successfully loaded trigger configuration")
        log_info(f"  Version: {config.get('version', 'unknown')}")
        log_info(f"  Calibration date: {config.get('calibration_date', 'unknown')}")
        log_info(f"  Data period: {config.get('data_period', 'unknown')}")

        # Log target trigger rates
        target_rates = config.get("target_trigger_rates", {})
        log_info("  Target trigger rates:")
        log_info(f"    Flood: {target_rates.get('flood', 0)*100:.1f}%")
        log_info(f"    Drought: {target_rates.get('drought', 0)*100:.1f}%")
        log_info(f"    Crop failure: {target_rates.get('crop_failure', 0)*100:.1f}%")

        return config

    except yaml.YAMLError as e:
        log_error(f"Error parsing YAML configuration: {e}")
        log_warning("Using default trigger thresholds")
        return _get_default_config()

    except ValidationError as e:
        log_error(f"Pydantic validation error: {e}")
        log_warning("Using default trigger thresholds")
        return _get_default_config()

    except Exception as e:
        log_error(f"Unexpected error loading configuration: {type(e).__name__}: {e}")
        log_warning("Using default trigger thresholds")
        return _get_default_config()


def validate_trigger_config(config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate trigger configuration for correctness and completeness.

    Performs comprehensive validation of the trigger configuration including:
    - Required field presence checks
    - Data type validation
    - Threshold range validation
    - Metadata completeness checks
    - Rationale and data source documentation

    Parameters
    ----------
    config : Dict
        Configuration dictionary to validate. Should contain all required
        fields as defined in the YAML schema.

    Returns
    -------
    Tuple[bool, List[str]]
        Tuple containing:
        - is_valid (bool): True if configuration is valid, False otherwise
        - errors (List[str]): List of validation error messages (empty if valid)

    Examples
    --------
    >>> config = load_trigger_config()
    >>> is_valid, errors = validate_trigger_config(config)
    >>> if not is_valid:
    ...     for error in errors:
    ...         print(f"Error: {error}")

    Notes
    -----
    Validation checks include:
    1. Required top-level fields (version, calibration_date, etc.)
    2. Target trigger rates within acceptable ranges
    3. All trigger type configurations present
    4. Threshold values within reasonable ranges
    5. Rationale and data sources documented
    6. Pydantic model validation for structure

    Requirements: 7.2, 7.4
    """
    errors = []
    warnings = []

    # ========================================================================
    # 1. Check required top-level fields
    # ========================================================================
    required_fields = [
        "version",
        "calibration_date",
        "data_period",
        "target_trigger_rates",
        "flood_triggers",
        "drought_triggers",
        "crop_failure_triggers",
    ]

    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required top-level field: '{field}'")

    # If critical fields are missing, return early
    if errors:
        return False, errors

    # ========================================================================
    # 2. Validate using Pydantic models
    # ========================================================================
    try:
        # Attempt to validate with pydantic model
        TriggerThresholdsConfig(**config)  # noqa: F841
        log_info("✓ Pydantic validation passed")
    except ValidationError as e:
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(f"Pydantic validation error in '{field_path}': {error['msg']}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected validation error: {type(e).__name__}: {e}")
        return False, errors

    # ========================================================================
    # 3. Validate target trigger rates
    # ========================================================================
    target_rates = config.get("target_trigger_rates", {})

    expected_rates = {
        "flood": (0.05, 0.15),  # 5-15% acceptable range
        "drought": (0.08, 0.20),  # 8-20% acceptable range
        "crop_failure": (0.03, 0.10),  # 3-10% acceptable range
    }

    for trigger_type, (min_rate, max_rate) in expected_rates.items():
        if trigger_type not in target_rates:
            errors.append(f"Missing target rate for '{trigger_type}'")
        else:
            rate = target_rates[trigger_type]
            if not isinstance(rate, (int, float)):
                errors.append(f"Target rate for '{trigger_type}' must be numeric, got {type(rate).__name__}")
            elif rate <= 0 or rate >= 1:
                errors.append(f"Target rate for '{trigger_type}' must be between 0 and 1, got {rate}")
            elif rate < min_rate or rate > max_rate:
                warnings.append(
                    f"Target rate for '{trigger_type}' ({rate*100:.1f}%) is outside "
                    f"recommended range ({min_rate*100:.1f}%-{max_rate*100:.1f}%)"
                )

    # ========================================================================
    # 4. Validate flood trigger configuration
    # ========================================================================
    flood_config = config.get("flood_triggers", {})

    # Check required fields
    required_flood_fields = ["daily_rainfall_mm", "rainfall_7day_mm", "heavy_rain_days_7day", "rainfall_percentile"]

    for field in required_flood_fields:
        if field not in flood_config:
            errors.append(f"Missing flood trigger field: '{field}'")

    # Validate threshold ranges
    if "daily_rainfall_mm" in flood_config:
        daily_config = flood_config["daily_rainfall_mm"]
        threshold = daily_config.get("threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("Daily rainfall threshold must be numeric")
            elif threshold < 0 or threshold > 1000:
                errors.append(f"Daily rainfall threshold out of range: {threshold}mm (expected 0-1000mm)")

        # Check for rationale (required field)
        if not daily_config.get("rationale") or daily_config.get("rationale") == "TBD":
            errors.append("Daily rainfall threshold missing rationale documentation")

    if "rainfall_7day_mm" in flood_config:
        day7_config = flood_config["rainfall_7day_mm"]
        threshold = day7_config.get("threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("7-day rainfall threshold must be numeric")
            elif threshold < 0 or threshold > 2000:
                errors.append(f"7-day rainfall threshold out of range: {threshold}mm (expected 0-2000mm)")

    # ========================================================================
    # 5. Validate drought trigger configuration
    # ========================================================================
    drought_config = config.get("drought_triggers", {})

    # Check required fields
    required_drought_fields = ["spi_30day", "consecutive_dry_days", "rainfall_deficit_pct"]

    for field in required_drought_fields:
        if field not in drought_config:
            errors.append(f"Missing drought trigger field: '{field}'")

    # Validate SPI threshold
    if "spi_30day" in drought_config:
        spi_config = drought_config["spi_30day"]
        threshold = spi_config.get("threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("SPI threshold must be numeric")
            elif threshold < -5 or threshold > 0:
                errors.append(f"SPI threshold out of range: {threshold} (expected -5 to 0)")
            elif threshold > -1.0:
                warnings.append(f"SPI threshold ({threshold}) may be too lenient for severe drought")

    # Validate consecutive dry days
    if "consecutive_dry_days" in drought_config:
        dry_days_config = drought_config["consecutive_dry_days"]
        wet_threshold = dry_days_config.get("wet_season_threshold")
        dry_threshold = dry_days_config.get("dry_season_threshold")

        if wet_threshold is not None:
            if not isinstance(wet_threshold, (int, float)):
                errors.append("Wet season dry days threshold must be numeric")
            elif wet_threshold < 7 or wet_threshold > 90:
                errors.append(
                    f"Wet season dry days threshold out of range: {wet_threshold} (expected 7-90 days)"
                )

        if dry_threshold is not None:
            if not isinstance(dry_threshold, (int, float)):
                errors.append("Dry season dry days threshold must be numeric")
            elif dry_threshold < 7 or dry_threshold > 120:
                errors.append(
                    f"Dry season dry days threshold out of range: {dry_threshold} (expected 7-120 days)"
                )

    # ========================================================================
    # 6. Validate crop failure trigger configuration
    # ========================================================================
    crop_config = config.get("crop_failure_triggers", {})

    # Check required fields
    required_crop_fields = ["vci_threshold", "ndvi_anomaly_std", "crop_failure_risk_score"]

    for field in required_crop_fields:
        if field not in crop_config:
            errors.append(f"Missing crop failure trigger field: '{field}'")

    # Validate VCI threshold
    if "vci_threshold" in crop_config:
        vci_config = crop_config["vci_threshold"]
        critical = vci_config.get("critical")
        severe = vci_config.get("severe")
        duration = vci_config.get("duration_days")

        if critical is not None:
            if not isinstance(critical, (int, float)):
                errors.append("VCI critical threshold must be numeric")
            elif critical < 0 or critical > 100:
                errors.append(f"VCI critical threshold out of range: {critical} (expected 0-100)")

        if severe is not None:
            if not isinstance(severe, (int, float)):
                errors.append("VCI severe threshold must be numeric")
            elif severe < 0 or severe > 100:
                errors.append(f"VCI severe threshold out of range: {severe} (expected 0-100)")

        if duration is not None:
            if not isinstance(duration, (int, float)):
                errors.append("VCI duration must be numeric")
            elif duration < 1 or duration > 90:
                errors.append(f"VCI duration out of range: {duration} (expected 1-90 days)")

    # Validate NDVI anomaly threshold
    if "ndvi_anomaly_std" in crop_config:
        ndvi_config = crop_config["ndvi_anomaly_std"]
        threshold = ndvi_config.get("threshold")
        duration = ndvi_config.get("duration_days")

        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("NDVI anomaly threshold must be numeric")
            elif threshold < -5 or threshold > 0:
                errors.append(f"NDVI anomaly threshold out of range: {threshold} (expected -5 to 0 std)")

    # ========================================================================
    # 7. Check metadata completeness
    # ========================================================================
    version = config.get("version", "")
    calibration_date = config.get("calibration_date", "")
    data_period = config.get("data_period", "")

    if version == "" or version == "TBD":
        warnings.append("Configuration version not set")

    if calibration_date == "" or calibration_date == "TBD":
        warnings.append("Calibration date not set - configuration may not be calibrated yet")

    if data_period == "" or data_period == "TBD":
        warnings.append("Data period not set - unable to verify calibration data source")

    # ========================================================================
    # 8. Log warnings (non-fatal issues)
    # ========================================================================
    if warnings:
        log_warning(f"Configuration validation warnings ({len(warnings)}):")
        for warning in warnings:
            log_warning(f"  - {warning}")

    # ========================================================================
    # 9. Return validation result
    # ========================================================================
    is_valid = len(errors) == 0

    if is_valid:
        log_info("✓ Configuration validation passed")
        if warnings:
            log_info(f"  Note: {len(warnings)} warnings (non-fatal)")
    else:
        log_error(f"✗ Configuration validation failed with {len(errors)} errors")

    return is_valid, errors


def _get_default_config() -> Dict:
    """
    Get scientifically-justified default trigger thresholds.

    Provides fallback configuration when the main configuration file is missing
    or invalid. These defaults are based on international standards and best
    practices for parametric insurance.

    Returns
    -------
    Dict
        Dictionary with default configuration containing:
        - Conservative thresholds based on WMO and FAO standards
        - Target trigger rates for financial sustainability
        - Metadata indicating this is a default configuration

    Notes
    -----
    Default thresholds are based on:
    - WMO Standardized Precipitation Index (SPI) guidelines
    - FAO Vegetation Condition Index (VCI) methodology
    - General parametric insurance best practices
    - Conservative values to prevent over-triggering

    These defaults should be replaced with calibrated values based on
    historical climate data for the specific region.

    Requirements: 7.3
    """
    log_info("Using scientifically-justified default trigger thresholds")
    log_warning("Default thresholds are conservative - calibration recommended")

    return {
        "version": "1.0.0-default",
        "calibration_date": "default",
        "data_period": "N/A",
        "target_trigger_rates": {"flood": 0.10, "drought": 0.12, "crop_failure": 0.06},
        "flood_triggers": {
            "daily_rainfall_mm": {
                "threshold": 150,
                "rationale": "Default extreme rainfall threshold",
                "data_source": "WMO guidelines",
            },
            "rainfall_7day_mm": {
                "threshold": 250,
                "rationale": "Default sustained heavy rainfall threshold",
                "data_source": "WMO guidelines",
            },
            "heavy_rain_days_7day": {
                "threshold": 5,
                "heavy_rain_definition_mm": 50,
                "rationale": "Default multiple heavy rain days threshold",
            },
            "rainfall_percentile": {"threshold": 99, "rationale": "Default extreme rainfall percentile"},
        },
        "drought_triggers": {
            "spi_30day": {
                "threshold": -1.5,
                "rationale": "WMO severe drought classification",
                "data_source": "WMO SPI guidelines",
            },
            "consecutive_dry_days": {
                "wet_season_threshold": 35,
                "dry_season_threshold": 45,
                "dry_day_definition_mm": 1.0,
                "rationale": "Default extended dry period thresholds",
            },
            "rainfall_deficit_pct": {"threshold": 50, "rationale": "Default significant rainfall deficit"},
        },
        "crop_failure_triggers": {
            "vci_threshold": {
                "critical": 20,
                "severe": 35,
                "duration_days": 30,
                "rationale": "FAO crop stress thresholds",
                "data_source": "FAO VCI methodology",
            },
            "ndvi_anomaly_std": {
                "threshold": -2.0,
                "duration_days": 21,
                "rationale": "Default significant vegetation stress",
            },
            "crop_failure_risk_score": {"threshold": 75, "rationale": "Default high crop failure probability"},
        },
        "regional_adjustments": {"enabled": False},
    }
