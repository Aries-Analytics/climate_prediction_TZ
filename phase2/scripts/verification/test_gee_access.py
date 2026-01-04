"""Test Google Earth Engine access with current credentials"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

import ee

print("Testing Google Earth Engine access...\n")

# Get project from environment
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
print(f"Project ID from .env: {project_id}\n")

# Try different initialization methods
methods = [
    (f"With project '{project_id}'", lambda: ee.Initialize(project=project_id)),
    ("Default (no project)", lambda: ee.Initialize()),
    ("High-volume endpoint", lambda: ee.Initialize(project=project_id, opt_url="https://earthengine-highvolume.googleapis.com")),
]

success = False
for name, init_func in methods:
    print(f"Trying: {name}")
    try:
        init_func()
        print(f"  ✓ Initialized successfully!")

        # Try a simple query with the correct MODIS 061 version
        print("  Testing MODIS data access...")
        collection = ee.ImageCollection("MODIS/061/MOD13A2")
        
        # Get first image from 2023
        image = collection.filterDate("2023-01-01", "2023-02-01").first()
        info = image.getInfo()
        
        if info:
            print(f"  ✓ Can access MODIS/061/MOD13A2 data!")
            print(f"  ✓ Image ID: {info.get('id', 'unknown')}")
            success = True
            break
    except Exception as e:
        print(f"  ✗ Failed: {str(e)[:150]}")
    print()

if success:
    print("\n" + "="*50)
    print("✓ Google Earth Engine is properly configured!")
    print("="*50)
    sys.exit(0)
else:
    print("\n" + "="*50)
    print("✗ GEE initialization failed. Try running:")
    print("  earthengine authenticate")
    print("="*50)
    sys.exit(1)
