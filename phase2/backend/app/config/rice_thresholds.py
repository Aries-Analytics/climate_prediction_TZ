"""
Kilombero Valley Rice Calendar & Thresholds for Insurance Triggers.
Source: Research on Morogoro Rice Production Seasons (Jan Planting).

This configuration replaces dynamic planting date logic with robust calendar-based
phenology stages for the two main growing seasons in the region.
"""

# Map Months to Growth Stages for Main Wet Season (Jan Planting)
# Based on: Planting Jan -> Harvest June
KILOMBERO_WET_SEASON = {
    1: 'germination',      # January: Planting/Germination (Days 1-30)
    2: 'vegetative',       # February: Vegetative Growth (Days 31-59)
    3: 'vegetative',       # March: Late Vegetative/Tillering (Days 60-90)
    4: 'flowering',        # April: Booting/Flowering (CRITICAL) (Days 91-120)
    5: 'grain_fill',       # May: Maturity/Grain Fill (Days 121-151)
    6: 'harvesting',       # June: Harvesting (Days 152+)
}

# Dry Season (Irrigated Only) - July Planting -> Dec Harvest
KILOMBERO_DRY_SEASON = {
    7: 'germination',      # July
    8: 'vegetative',       # August
    9: 'vegetative',       # September
    10: 'flowering',       # October (CRITICAL)
    11: 'grain_fill',      # November
    12: 'harvesting',      # December
}

# Critical Rainfall Thresholds (mm/month)
# Derived from TARI & FAO requirements for rainfed rice
RAINFALL_THRESHOLDS = {
    'germination': {
        'min': 50.0,       # Seeds need moisture to sprout
        'optimal': 100.0,
        'excessive': 250.0 # Risk of washing away seeds
    },
    'vegetative': {
        'min': 100.0,      # Needs steady moisture for tillering
        'optimal': 150.0,
        'excessive': 400.0
    },
    'flowering': {
        'min': 120.0,      # MOST CRITICAL STAGE - Yield determinant
        'optimal': 200.0,  # High water requirement
        'excessive': 500.0 # Risk of lodging/fungal issues
    },
    'grain_fill': {
        'min': 60.0,       # Needs tapering moisture
        'optimal': 100.0,
        'excessive': 200.0
    },
    'harvesting': {
        'min': 0.0,        # Needs dry weather
        'optimal': 20.0,
        'excessive': 80.0  # Risk of grain spoilage/difficult harvest
    },
    'off_season': {
        'min': 0.0,
        'optimal': 0.0,
        'excessive': 9999.0
    }
}

def get_kilombero_stage(target_date, season_type='wet'):
    """
    Return the phenology stage for a given date based on Kilombero calendar.
    
    Args:
        target_date (date): The forecast target date
        season_type (str): 'wet' (main) or 'dry' (irrigated)
        
    Returns:
        str: Stage name (e.g., 'flowering') or 'off_season'
    """
    month = target_date.month
    
    if season_type == 'dry':
        return KILOMBERO_DRY_SEASON.get(month, 'off_season')
    
    # Default to main Wet Season
    return KILOMBERO_WET_SEASON.get(month, 'off_season')
