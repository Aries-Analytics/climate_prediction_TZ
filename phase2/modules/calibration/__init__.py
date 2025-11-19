"""
Calibration module for insurance trigger threshold analysis and optimization.

This module provides functionality for:
- Analyzing historical climate data to determine appropriate trigger thresholds
- Calibrating trigger thresholds to achieve target activation rates
- Validating trigger performance against known extreme weather events
- Loading and validating trigger configuration files
"""

from modules.calibration.config_loader import load_trigger_config, validate_trigger_config
from modules.calibration.analyze_thresholds import (
    analyze_rainfall_distribution,
    analyze_drought_indicators,
    analyze_vegetation_stress,
    generate_threshold_report
)
from modules.calibration.calibrate_triggers import (
    calibrate_flood_triggers,
    calibrate_drought_triggers,
    calibrate_crop_failure_triggers,
    simulate_trigger_rates
)

__all__ = [
    'load_trigger_config',
    'validate_trigger_config',
    'analyze_rainfall_distribution',
    'analyze_drought_indicators',
    'analyze_vegetation_stress',
    'generate_threshold_report',
    'calibrate_flood_triggers',
    'calibrate_drought_triggers',
    'calibrate_crop_failure_triggers',
    'simulate_trigger_rates',
]
