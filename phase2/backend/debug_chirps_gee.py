"""
Debug script to check CHIRPS data availability in Google Earth Engine
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import ee
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize GEE
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
    ee.Initialize(project=project_id)
    print(f"✓ Google Earth Engine initialized with project: {project_id}")
    
    # Tanzania bounds
    bounds = {
        "lat_min": -11.75,
        "lat_max": -0.99,
        "lon_min": 29.34,
        "lon_max": 40.44,
    }
    
    region = ee.Geometry.Rectangle([
        bounds["lon_min"], 
        bounds["lat_min"], 
        bounds["lon_max"], 
        bounds["lat_max"]
    ])
    
    # Get CHIRPS collection
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    
    # Check what dates are available
    print("\n" + "=" * 70)
    print("CHIRPS DATA AVAILABILITY CHECK")
    print("=" * 70)
    
    # Get the date range of the collection
    dates = chirps.aggregate_array('system:time_start').getInfo()
    if dates:
        from datetime import datetime
        first_date = datetime.fromtimestamp(min(dates) / 1000)
        last_date = datetime.fromtimestamp(max(dates) / 1000)
        print(f"\nCHIRPS Collection Date Range:")
        print(f"  First available: {first_date.strftime('%Y-%m-%d')}")
        print(f"  Last available:  {last_date.strftime('%Y-%m-%d')}")
    
    # Test specific months in 2025
    print("\n" + "=" * 70)
    print("TESTING 2025 DATA AVAILABILITY")
    print("=" * 70)
    
    test_months = [
        (2025, 6, "June"),
        (2025, 7, "July"),
        (2025, 8, "August"),
        (2025, 9, "September"),
        (2025, 10, "October"),
        (2025, 11, "November"),
    ]
    
    for year, month, month_name in test_months:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        # Filter to this month
        monthly = chirps.filterDate(start_date, end_date).filterBounds(region)
        
        # Count images
        count = monthly.size().getInfo()
        
        print(f"\n{month_name} {year}:")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Images found: {count}")
        
        if count > 0:
            # Try to get the data
            try:
                monthly_sum = monthly.sum()
                stats = monthly_sum.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=5000,
                    maxPixels=1e9,
                )
                
                # Check what keys are available
                keys = stats.keys().getInfo()
                print(f"  Available keys: {keys}")
                
                # Try to get precipitation
                if 'precipitation' in keys:
                    rainfall = stats.get('precipitation').getInfo()
                    print(f"  ✓ Rainfall: {rainfall:.2f} mm")
                else:
                    print(f"  ❌ 'precipitation' key NOT found!")
                    print(f"  Available data: {stats.getInfo()}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"  ❌ No images available for this period")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    print("\nPossible issues:")
    print("1. CHIRPS data has a lag (typically 1-2 weeks)")
    print("2. Recent months may not be available yet")
    print("3. GEE collection may be updating")
    print("4. Region filter may be excluding data")
    
except ImportError:
    print("❌ Google Earth Engine not installed")
    print("Install with: pip install earthengine-api")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
