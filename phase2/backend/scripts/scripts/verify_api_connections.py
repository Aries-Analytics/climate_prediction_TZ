"""
API Connection Verification Script

Tests connectivity and authentication for all data sources:
- NASA POWER
- CHIRPS
- ERA5
- NDVI (MODIS)
- Ocean Indices (NOAA PSL)
"""

import os
import sys
from pathlib import Path
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load environment variables
load_dotenv()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def test_nasa_power():
    """Test NASA POWER API connection"""
    print_header("NASA POWER API")
    
    api_url = os.getenv("NASA_API_URL", "https://power.larc.nasa.gov/api/temporal/monthly/point")
    api_key = os.getenv("NASA_API_KEY")
    
    print(f"API URL: {api_url}")
    print(f"API Key: {'Set' if api_key and api_key != 'your_nasa_power_api_key_here' else 'NOT SET'}")
    
    # NASA POWER doesn't require API key for basic access
    # Test with Tanzania coordinates
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": 34.8888,
        "latitude": -6.3690,
        "start": "2023",
        "end": "2023",
        "format": "JSON"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "properties" in data and "parameter" in data["properties"]:
                print_success("NASA POWER API is accessible")
                print_success(f"Retrieved data for parameters: {list(data['properties']['parameter'].keys())}")
                return True
            else:
                print_error("NASA POWER API returned unexpected format")
                return False
        else:
            print_error(f"NASA POWER API returned status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("NASA POWER API request timed out")
        return False
    except Exception as e:
        print_error(f"NASA POWER API error: {str(e)}")
        return False


def test_chirps():
    """Test CHIRPS data access"""
    print_header("CHIRPS Rainfall Data")
    
    base_url = os.getenv("CHIRPS_BASE_URL", "https://data.chc.ucsb.edu/products/CHIRPS-2.0")
    
    print(f"Base URL: {base_url}")
    print("Note: CHIRPS is publicly accessible, no API key required")
    
    # Test access to a recent monthly file
    test_url = f"{base_url}/global_monthly/tifs/chirps-v2.0.2023.01.tif.gz"
    
    try:
        response = requests.head(test_url, timeout=30)
        
        if response.status_code == 200:
            print_success("CHIRPS data portal is accessible")
            print_success(f"Test file exists: chirps-v2.0.2023.01.tif.gz")
            return True
        elif response.status_code == 404:
            # Try the base URL instead
            response = requests.head(base_url, timeout=30)
            if response.status_code == 200:
                print_success("CHIRPS base URL is accessible")
                print_warning("Specific test file not found (may be expected)")
                return True
            else:
                print_error(f"CHIRPS portal returned status code: {response.status_code}")
                return False
        else:
            print_error(f"CHIRPS portal returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("CHIRPS request timed out")
        return False
    except Exception as e:
        print_error(f"CHIRPS error: {str(e)}")
        return False


def test_era5():
    """Test ERA5 API access"""
    print_header("ERA5 Climate Data")
    
    api_key = os.getenv("ERA5_API_KEY")
    
    print(f"API Key: {'Set' if api_key and api_key != 'your_era5_api_key_here' else 'NOT SET'}")
    
    if not api_key or api_key == "your_era5_api_key_here":
        print_warning("ERA5 API key not configured")
        print("To use ERA5 data:")
        print("1. Register at https://cds.climate.copernicus.eu/")
        print("2. Get your API key from your profile")
        print("3. Set ERA5_API_KEY in .env file")
        return False
    
    # Test CDS API connection
    try:
        import cdsapi
        
        # Create client with API key
        c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api/v2", key=api_key)
        
        print_success("ERA5 CDS API client initialized")
        print_warning("Full data retrieval test skipped (would take too long)")
        print("Note: Actual data download will be tested during ingestion")
        return True
        
    except ImportError:
        print_error("cdsapi package not installed")
        print("Install with: pip install cdsapi")
        return False
    except Exception as e:
        print_error(f"ERA5 API error: {str(e)}")
        print("Check your API key and CDS registration")
        return False


def test_ndvi():
    """Test NDVI/MODIS data access"""
    print_header("NDVI/MODIS Data")
    
    source_url = os.getenv("NDVI_SOURCE_URL", "https://modis.gsfc.nasa.gov/data/")
    
    print(f"Source URL: {source_url}")
    print("Note: MODIS data typically accessed via NASA Earthdata")
    
    # Test MODIS website accessibility
    try:
        response = requests.head(source_url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            print_success("MODIS data portal is accessible")
            print_warning("Authentication required for data download")
            print("To download MODIS data:")
            print("1. Register at https://urs.earthdata.nasa.gov/")
            print("2. Configure credentials for data access")
            return True
        else:
            print_error(f"MODIS portal returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("MODIS request timed out")
        return False
    except Exception as e:
        print_error(f"MODIS error: {str(e)}")
        return False


def test_ocean_indices():
    """Test Ocean Indices data access"""
    print_header("Ocean & Atmospheric Indices (NOAA PSL)")
    
    source_url = os.getenv("OCEAN_INDICES_SOURCE_URL", "https://psl.noaa.gov/data/climateindices/list/")
    
    print(f"Source URL: {source_url}")
    print("Note: NOAA PSL data is publicly accessible")
    
    # Test specific index file (e.g., Niño 3.4)
    test_url = "https://psl.noaa.gov/data/correlation/nina34.data"
    
    try:
        response = requests.get(test_url, timeout=30)
        
        if response.status_code == 200:
            # Check if we got actual data
            content = response.text
            if len(content) > 100 and any(char.isdigit() for char in content):
                print_success("NOAA PSL data portal is accessible")
                print_success("Successfully retrieved Niño 3.4 index data")
                return True
            else:
                print_error("NOAA PSL returned unexpected content")
                return False
        else:
            print_error(f"NOAA PSL returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("NOAA PSL request timed out")
        return False
    except Exception as e:
        print_error(f"NOAA PSL error: {str(e)}")
        return False


def main():
    """Run all API verification tests"""
    print_header("API Connection Verification")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "NASA POWER": test_nasa_power(),
        "CHIRPS": test_chirps(),
        "ERA5": test_era5(),
        "NDVI/MODIS": test_ndvi(),
        "Ocean Indices": test_ocean_indices()
    }
    
    # Summary
    print_header("Verification Summary")
    
    for source, status in results.items():
        if status:
            print_success(f"{source}: Connected")
        else:
            print_error(f"{source}: Failed or Not Configured")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{BLUE}Results: {passed}/{total} data sources verified{RESET}")
    
    if passed == total:
        print_success("\nAll API connections verified successfully!")
        return 0
    elif passed > 0:
        print_warning(f"\n{passed} out of {total} connections verified")
        print("Review failed connections above for configuration steps")
        return 1
    else:
        print_error("\nNo API connections could be verified")
        print("Please check your .env configuration and network connection")
        return 2


if __name__ == "__main__":
    sys.exit(main())
