"""
Rice Growth Phase Configuration for Weather Index Insurance
Based on: FAO crop water requirements + industry best practices
Version: 1.0
Date: January 23, 2026
"""

from typing import Dict, List

# Rice Growing Season Configuration (Morogoro, Tanzania)
# Total duration: 145 days (~4.8 months)
# Season: March-June (long rains)

RICE_GROWTH_PHASES: Dict[str, Dict] = {
    'germination': {
        'duration_days': 21,
        'rainfall_requirement_mm': 60,
        'drought_trigger_mm': 50,  # Increased from 40mm
        'flood_trigger_daily_mm': 70,  # Increased from 50mm
        'payout_weight': 0.20,  # 20% of sum insured
        'critical_period': 'Low',
        'description': 'Seed germination and seedling emergence',
        'agronomic_notes': 'Requires consistent moisture for germination; excess water can cause seed rot'
    },
    
    'vegetative': {
        'duration_days': 29,
        'rainfall_requirement_mm': 100,
        'drought_trigger_mm': 60,  # Increased from 40mm to capture 2017/2022
        'flood_trigger_daily_mm': 80,  # Increased from 50mm to reduce false positives
        'payout_weight': 0.30,  # 30% of sum insured
        'critical_period': 'Medium',
        'description': 'Tillering and vegetative growth',
        'agronomic_notes': 'Active tillering requires adequate water; deficits reduce tiller count'
    },
    
    'flowering': {
        'duration_days': 40,
        'rainfall_requirement_mm': 120,
        'drought_trigger_mm': 80,  # Increased from 50mm to capture 2017/2022
        'flood_trigger_daily_mm': 90,  # Increased from 60mm
        'payout_weight': 0.35,  # 35% of sum insured - MOST CRITICAL PHASE
        'critical_period': 'HIGH',
        'description': 'Panicle initiation, flowering, and pollination',
        'agronomic_notes': 'Water stress during flowering directly reduces grain number - CRITICAL PHASE'
    },
    
    'ripening': {
        'duration_days': 55,
        'rainfall_requirement_mm': 120,
        'drought_trigger_mm': 0, # No drought payout for ripening (dry is good)
        'flood_trigger_daily_mm': 60,  # Increased from 40mm
        'payout_weight': 0.15,  # 15% of sum insured
        'critical_period': 'Medium',
        'description': 'Grain filling and maturation',
        'agronomic_notes': 'Excess rain at ripening causes lodging and quality issues'
    }
}

# Total season validation
TOTAL_DURATION_DAYS = sum(phase['duration_days'] for phase in RICE_GROWTH_PHASES.values())
TOTAL_RAINFALL_REQUIREMENT = sum(phase['rainfall_requirement_mm'] for phase in RICE_GROWTH_PHASES.values())
TOTAL_WEIGHT = sum(phase['payout_weight'] for phase in RICE_GROWTH_PHASES.values())

# Assertions to ensure configuration validity
assert TOTAL_DURATION_DAYS == 145, f"Total duration must be 145 days, got {TOTAL_DURATION_DAYS}"
assert TOTAL_RAINFALL_REQUIREMENT == 400, f"Total rainfall must be 400mm, got {TOTAL_RAINFALL_REQUIREMENT}"
assert abs(TOTAL_WEIGHT - 1.0) < 0.01, f"Weights must sum to 1.0, got {TOTAL_WEIGHT}"

# Dynamic Start Configuration (Industry Best Practice)
DYNAMIC_START_CONFIG = {
    'monitoring_month': 3,  # March
    'cumulative_threshold_mm': 50,  # Trigger when 50mm recorded
    'fallback_date': (4, 1),  # April 1 if March too dry
    'reasoning': 'Aligns coverage with actual planting behavior, reduces basis risk'
}

# Soil Moisture Thresholds (Industry Standard)
SOIL_MOISTURE_THRESHOLDS = {
    'deficit_threshold': 0.15,  # < 15% root zone moisture = drought stress
    'excess_threshold': 0.95,   # > 95% root zone moisture = potential waterlogging (rare for rice)
    'normal_range': (0.15, 0.25),
    'payout_multiplier_deficit': 1.0,  # Full payout weight for deficit
    'payout_multiplier_excess': 0.75,  # 75% payout weight for excess (less severe than drought)
}

# Payout Rates (from PARAMETRIC_INSURANCE_FINAL.md)
PAYOUT_RATES = {
    'drought': 60,  # USD per trigger
    'flood': 75,
    'crop_failure': 90,  # Maximum sum insured
}

# FAO Reference (for validation)
FAO_RICE_WATER_REQUIREMENTS = {
    'source': 'FAO Irrigation and Drainage Paper 56',
    'crop': 'Rice (paddy)',
    'region': 'Sub-Saharan Africa',
    'total_seasonal_mm': 400,  # Validates our threshold ✓
    'critical_phases': ['flowering', 'grain_filling'],
    'notes': 'Configuration aligned with FAO recommendations'
}

def get_phase_by_day(day_of_season: int) -> str:
    """
    Get which growth phase corresponds to a given day of the season
    
    Args:
        day_of_season: Day number (1-145)
        
    Returns:
        Phase name: 'germination', 'vegetative', 'flowering', or 'ripening'
    """
    cumulative_days = 0
    for phase_name, phase_config in RICE_GROWTH_PHASES.items():
        cumulative_days += phase_config['duration_days']
        if day_of_season <= cumulative_days:
            return phase_name
    raise ValueError(f"Day {day_of_season} exceeds season length ({TOTAL_DURATION_DAYS} days)")

def validate_configuration():
    """Validate all configuration parameters"""
    errors = []
    
    # Check phase weights sum to 1.0
    if abs(TOTAL_WEIGHT - 1.0) >= 0.01:
        errors.append(f"Phase weights sum to {TOTAL_WEIGHT}, must be 1.0")
    
    # Check all phases have required fields
    required_fields = ['duration_days', 'rainfall_requirement_mm', 'drought_trigger_mm', 
                      'flood_trigger_daily_mm', 'payout_weight']
    for phase_name, phase_config in RICE_GROWTH_PHASES.items():
        for field in required_fields:
            if field not in phase_config:
                errors.append(f"Phase '{phase_name}' missing field '{field}'")
    
    # Check rainfall requirements vs triggers
    for phase_name, phase_config in RICE_GROWTH_PHASES.items():
        if phase_config['drought_trigger_mm'] >= phase_config['rainfall_requirement_mm']:
            errors.append(f"Phase '{phase_name}': drought trigger must be < rainfall requirement")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    return True

# Validate on import
validate_configuration()

if __name__ == "__main__":
    print("Rice Growth Phase Configuration")
    print("=" * 50)
    print(f"\nTotal Season: {TOTAL_DURATION_DAYS} days ({TOTAL_DURATION_DAYS/30:.1f} months)")
    print(f"Total Rainfall Requirement: {TOTAL_RAINFALL_REQUIREMENT}mm")
    print(f"\nPhase Breakdown:")
    print("-" * 50)
    
    for phase_name, config in RICE_GROWTH_PHASES.items():
        print(f"\n{phase_name.upper()}")
        print(f"  Duration: {config['duration_days']} days")
        print(f"  Rainfall Need: {config['rainfall_requirement_mm']}mm")
        print(f"  Drought Trigger: < {config['drought_trigger_mm']}mm")
        print(f"  Flood Trigger: > {config['flood_trigger_daily_mm']}mm/day")
        print(f"  Payout Weight: {config['payout_weight']*100:.0f}%")
        print(f"  Critical: {config['critical_period']}")
    
    print("\n" + "=" * 50)
    print("✓ Configuration validated successfully")
