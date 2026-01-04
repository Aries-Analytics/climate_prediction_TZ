"""
Test script to verify ingestion module integration with orchestrator.

This script tests that the updated ingestion modules work correctly with the
pipeline orchestrator's interface.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import ingestion functions
from modules.ingestion.chirps_ingestion import ingest_chirps
from modules.ingestion.nasa_power_ingestion import ingest_nasa_power
from modules.ingestion.era5_ingestion import ingest_era5
from modules.ingestion.ndvi_ingestion import ingest_ndvi
from modules.ingestion.ocean_indices_ingestion import ingest_ocean_indices


def test_ingestion_interface():
    """Test that all ingestion modules have the correct interface."""
    
    print("=" * 60)
    print("Testing Ingestion Module Integration")
    print("=" * 60)
    
    # Create a test database session (in-memory SQLite for testing)
    engine = create_engine("sqlite:///:memory:")
    
    # Create tables
    from backend.app.models.climate_data import Base
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Test date range
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2020, 3, 31)
    
    modules_to_test = [
        ("CHIRPS", ingest_chirps),
        ("NASA POWER", ingest_nasa_power),
        ("ERA5", ingest_era5),
        ("NDVI", ingest_ndvi),
        ("Ocean Indices", ingest_ocean_indices),
    ]
    
    results = []
    
    for module_name, ingest_func in modules_to_test:
        print(f"\n{'─' * 60}")
        print(f"Testing {module_name}...")
        print(f"{'─' * 60}")
        
        try:
            # Test the function signature
            records_fetched, records_stored = ingest_func(
                db=db,
                start_date=start_date,
                end_date=end_date,
                incremental=False
            )
            
            # Verify return type
            assert isinstance(records_fetched, int), f"{module_name}: records_fetched must be int"
            assert isinstance(records_stored, int), f"{module_name}: records_stored must be int"
            assert records_fetched >= 0, f"{module_name}: records_fetched must be non-negative"
            assert records_stored >= 0, f"{module_name}: records_stored must be non-negative"
            
            print(f"✓ {module_name} interface test PASSED")
            print(f"  - Records fetched: {records_fetched}")
            print(f"  - Records stored: {records_stored}")
            
            results.append((module_name, "PASS", records_fetched, records_stored))
            
        except Exception as e:
            print(f"✗ {module_name} interface test FAILED")
            print(f"  Error: {e}")
            results.append((module_name, "FAIL", 0, 0))
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
    
    for module_name, status, fetched, stored in results:
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {module_name:20s} {status:6s} (fetched: {fetched:4d}, stored: {stored:4d})")
    
    passed = sum(1 for _, status, _, _ in results if status == "PASS")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} modules passed")
    
    db.close()
    
    return passed == total


if __name__ == "__main__":
    success = test_ingestion_interface()
    sys.exit(0 if success else 1)
