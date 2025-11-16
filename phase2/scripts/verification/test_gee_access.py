"""Test Google Earth Engine access with current credentials"""

import ee

print("Testing Google Earth Engine access...\n")

# Try different initialization methods
methods = [
    ("Default (no project)", lambda: ee.Initialize()),
    ("With ee-default-project", lambda: ee.Initialize(project="ee-default-project")),
    ("High-volume endpoint", lambda: ee.Initialize(opt_url="https://earthengine-highvolume.googleapis.com")),
]

for name, init_func in methods:
    print(f"Trying: {name}")
    try:
        init_func()
        print(f"  ✓ Success!")

        # Try a simple query
        image = ee.Image("MODIS/006/MOD13A2/2023_01_01")
        info = image.getInfo()
        print(f"  ✓ Can access MODIS data!")
        print(f"  Project used: {ee.data.getAssetRoots()}")
        break
    except Exception as e:
        print(f"  ✗ Failed: {str(e)[:100]}")
    print()
