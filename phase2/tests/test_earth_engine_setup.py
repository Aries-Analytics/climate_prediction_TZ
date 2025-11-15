"""
Test script to verify Google Earth Engine setup and access to data sources.
Run this after completing Earth Engine authentication.
"""

import sys
from datetime import datetime

import pytest

ee = pytest.importorskip("ee", reason="earthengine-api not installed")


def test_earth_engine_initialization():
    """Test if Earth Engine can be initialized."""
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized successfully!")
        return True
    except Exception as e:
        print(f"✗ Earth Engine initialization failed: {e}")
        print("\nPlease run: earthengine authenticate")
        return False


def test_chirps_access():
    """Test access to CHIRPS precipitation data."""
    try:
        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
        
        # Get a sample image
        sample = chirps.filterDate('2023-01-01', '2023-01-02').first()
        info = sample.getInfo()
        
        print("✓ CHIRPS data access successful!")
        print(f"  Sample image ID: {info['id']}")
        return True
    except Exception as e:
        print(f"✗ CHIRPS data access failed: {e}")
        return False


def test_modis_ndvi_access():
    """Test access to MODIS NDVI data."""
    try:
        modis = ee.ImageCollection('MODIS/006/MOD13Q1')
        
        # Get a sample image
        sample = modis.filterDate('2023-01-01', '2023-02-01').first()
        info = sample.getInfo()
        
        print("✓ MODIS NDVI data access successful!")
        print(f"  Sample image ID: {info['id']}")
        return True
    except Exception as e:
        print(f"✗ MODIS NDVI data access failed: {e}")
        return False


def test_tanzania_region():
    """Test querying data for Tanzania region."""
    try:
        # Tanzania bounding box (approximate)
        tanzania_bbox = ee.Geometry.Rectangle([29.0, -12.0, 41.0, -1.0])
        
        # Try to get CHIRPS data for Tanzania
        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate('2023-01-01', '2023-01-07') \
            .filterBounds(tanzania_bbox)
        
        count = chirps.size().getInfo()
        print(f"✓ Tanzania region query successful!")
        print(f"  Found {count} CHIRPS images for test period")
        return True
    except Exception as e:
        print(f"✗ Tanzania region query failed: {e}")
        return False


def main():
    """Run all Earth Engine setup tests."""
    print("=" * 60)
    print("Earth Engine Setup Verification")
    print("=" * 60)
    print()
    
    tests = [
        ("Earth Engine Initialization", test_earth_engine_initialization),
        ("CHIRPS Data Access", test_chirps_access),
        ("MODIS NDVI Data Access", test_modis_ndvi_access),
        ("Tanzania Region Query", test_tanzania_region),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        result = test_func()
        results.append(result)
        print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Your Earth Engine setup is ready.")
        print("\nNext steps:")
        print("1. Copy .env.template to .env")
        print("2. Add your Google Cloud Project ID to .env")
        print("3. Run your data ingestion modules")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
