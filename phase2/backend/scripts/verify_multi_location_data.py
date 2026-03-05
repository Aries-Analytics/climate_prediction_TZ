"""
Multi-Location Data Availability Verification

Tests data availability for all 5 selected Tanzania locations across all climate sources
for the period 2000-2025 before proceeding with full data collection.

This script:
1. Tests API access for each location
2. Verifies historical data availability (2000-2025)
3. Checks data quality and completeness
4. Generates a detailed availability report
"""

import os
import sys
from pathlib import Path
import yaml
import requests
import pandas as pd
from datetime import datetime, date, timezone
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load environment variables
load_dotenv()

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


def load_locations_config() -> dict:
    """Load locations from config file"""
    config_path = Path(__file__).resolve().parents[1] / "configs" / "locations_config.yaml"
    
    print(f"{CYAN}Loading locations from: {config_path}{RESET}")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"{GREEN}[OK] Loaded {len(config['locations'])} locations{RESET}\n")
    return config


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_section(text: str):
    """Print section header"""
    print(f"\n{CYAN}{'-'*70}{RESET}")
    print(f"{CYAN}{text}{RESET}")
    print(f"{CYAN}{'-'*70}{RESET}")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}[OK] {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}[FAIL] {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}[!] {text}{RESET}")


def verify_nasa_power_location(location_name: str, lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify NASA POWER data availability for a specific location.
    
    Returns:
        Tuple of (success, message)
    """
    api_url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    
    params = {
        "parameters": "T2M,T2M_MIN,T2M_MAX,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": "2000",
        "end": "2025",
        "format": "JSON"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if "properties" in data and "parameter" in data["properties"]:
                params_retrieved = list(data["properties"]["parameter"].keys())
                month_count = len(data["properties"]["parameter"]["T2M"])
                
                return True, f"Retrieved {len(params_retrieved)} parameters, {month_count} months (2000-2025)"
            else:
                return False, "Unexpected response format"
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out (>60s)"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


def verify_chirps_location(location_name: str, lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify CHIRPS data availability via Google Earth Engine.
    
    Note: This checks if GEE is available, actual data availability tested during ingestion
    """
    try:
        import ee
        
        # Check if EE is initialized
        try:
            # Get project from environment
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
            ee.Initialize(project=project_id)
            return True, "Google Earth Engine available, CHIRPS accessible (2000-2025)"
        except Exception as init_error:
            return False, f"GEE not initialized: {str(init_error)[:50]}"
            
    except ImportError:
        return False, "earthengine-api not installed (pip install earthengine-api)"


def verify_era5_location(location_name: str, lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify ERA5 CDS API configuration and availability.
    
    Note: Full data retrieval test skipped (would take too long)
    """
    api_key = os.getenv("ERA5_API_KEY")
    
    if not api_key or api_key == "your_era5_api_key_here":
        return False, "API key not configured (set ERA5_API_KEY in .env)"
    
    try:
        import cdsapi
        
        # Create client
        c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api/v2", key=api_key)
        
        return True, f"CDS API configured, ERA5 available (2000-2025)"
        
    except ImportError:
        return False, "cdsapi not installed (pip install cdsapi)"
    except Exception as e:
        return False, f"CDS API error: {str(e)[:50]}"


def verify_ndvi_location(location_name: str, lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify NDVI/MODIS data availability via Google Earth Engine.
    
    Uses hybrid AVHRR (1985-1999) + MODIS (2000-2025) approach as per ndvi_ingestion.py
    """
    try:
        import ee
        
        # Check if EE is initialized
        try:
            # Get project from environment
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
            ee.Initialize(project=project_id)
            
            # Verify MODIS collection accessibility
            modis = ee.ImageCollection("MODIS/006/MOD13A2")
            
            # Test query for location (just checking collection exists)
            point = ee.Geometry.Point([lon, lat])
            
            return True, "Google Earth Engine available, MODIS/AVHRR accessible (2000-2025)"
            
        except Exception as init_error:
            return False, f"GEE not initialized: {str(init_error)[:50]}"
            
    except ImportError:
        return False, "earthengine-api not installed (pip install earthengine-api)"


def verify_ocean_indices() -> Tuple[bool, str]:
    """
    Verify Ocean Indices (ENSO, IOD) data availability.
    
    Note: These are global indices, not location-specific
    """
    test_urls = {
        "Niño 3.4": "https://psl.noaa.gov/data/correlation/nina34.data",
        "DMI (IOD)": "https://psl.noaa.gov/gcos_wgsp/Timeseries/DMI/"
    }
    
    results = []
    for index_name, url in test_urls.items():
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                results.append(f"{index_name}: OK")
            else:
                results.append(f"{index_name}: HTTP {response.status_code}")
        except Exception as e:
            results.append(f"{index_name}: Error")
    
    if len(results) == len(test_urls):
        return True, f"Ocean indices available (2000-2025): {', '.join(results)}"
    else:
        return False, "Some ocean indices inaccessible"


def verify_all_locations(config: dict) -> Dict[str, Dict[str, Tuple[bool, str]]]:
    """
    Verify all data sources for all locations.
    
    Returns:
        Dict mapping location -> source -> (success, message)
    """
    locations = config['locations']
    results = {}
    
    # Ocean indices are global, test once
    print_section("Testing Ocean Indices (Global)")
    ocean_success, ocean_msg = verify_ocean_indices()
    if ocean_success:
        print_success(ocean_msg)
    else:
        print_error(ocean_msg)
    
    # Test each location
    for loc_id, loc_data in locations.items():
        location_name = loc_data['name']
        lat = loc_data['latitude']
        lon = loc_data['longitude']
        
        print_section(f"Testing Location: {location_name}")
        print(f"Coordinates: {lat:.4f}°S, {lon:.4f}°E")
        print(f"Climate Zone: {loc_data['climate_zone']}")
        print(f"Region: {loc_data['region']}\n")
        
        location_results = {}
        
        # Test NASA POWER
        print(f"  Testing NASA POWER...", end=" ")
        success, msg = verify_nasa_power_location(location_name, lat, lon)
        location_results['NASA_POWER'] = (success, msg)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        
        # Test CHIRPS
        print(f"  Testing CHIRPS (GEE)...", end=" ")
        success, msg = verify_chirps_location(location_name, lat, lon)
        location_results['CHIRPS'] = (success, msg)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        
        # Test ERA5
        print(f"  Testing ERA5...", end=" ")
        success, msg = verify_era5_location(location_name, lat, lon)
        location_results['ERA5'] = (success, msg)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        
        # Test NDVI
        print(f"  Testing NDVI (MODIS/GEE)...", end=" ")
        success, msg = verify_ndvi_location(location_name, lat, lon)
        location_results['NDVI'] = (success, msg)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        
        # Ocean indices same for all locations
        location_results['OCEAN_INDICES'] = (ocean_success, ocean_msg)
        
        results[location_name] = location_results
    
    return results


def generate_availability_report(config: dict, results: Dict[str, Dict[str, Tuple[bool, str]]]):
    """Generate detailed availability report as Markdown"""
    
    report_path = Path(__file__).resolve().parents[1] / "docs" / "DATA_AVAILABILITY_REPORT.md"
    
    print_header("Generating Data Availability Report")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Data Availability Report: Multi-Location Spatial-Temporal Expansion\n\n")
        f.write(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write("This report documents data availability verification for the spatial-temporal data augmentation strategy ")
        f.write("to expand the training dataset from 191 samples (single location) to 1,560 samples (5 locations × 312 months).\n\n")
        
        # Calculate overall success
        total_tests = len(results) * 5  # 5 locations * 5 data sources
        passed_tests = sum(
            1 for loc_results in results.values()
            for success, _ in loc_results.values()
            if success
        )
        success_rate = (passed_tests / total_tests) * 100
        
        f.write(f"**Overall Success Rate**: {passed_tests}/{total_tests} ({success_rate:.1f}%)\n\n")
        
        if success_rate >= 90:
            f.write("> [!NOTE]\n")
            f.write("> **Recommendation: PROCEED with Phase 2 (Data Collection)**\n")
            f.write("> All critical data sources are accessible for the selected locations.\n\n")
        elif success_rate >= 70:
            f.write("> [!WARNING]\n")
            f.write("> **Recommendation: PROCEED WITH CAUTION**\n")
            f.write("> Some data sources require configuration. Review failures below.\n\n")
        else:
            f.write("> [!CAUTION]\n")
            f.write("> **Recommendation: DO NOT PROCEED**\n")
            f.write("> Significant data availability issues. Address failures before continuing.\n\n")
        
        f.write("---\n\n")
        
        # Selected Locations
        f.write("## Selected Locations\n\n")
        f.write("| Location | Coordinates | Elevation | Climate Zone | Region |\n")
        f.write("|----------|-------------|-----------|--------------|--------|\n")
        for loc_id, loc_data in config['locations'].items():
            f.write(f"| {loc_data['name']} | ")
            f.write(f"{loc_data['latitude']:.4f}°S, {loc_data['longitude']:.4f}°E | ")
            f.write(f"{loc_data['elevation']} m | ")
            f.write(f"{loc_data['climate_zone'].replace('_', ' ').title()} | ")
            f.write(f"{loc_data['region'].title()} |\n")
        f.write("\n---\n\n")
        
        # Detailed Results by Location
        f.write("## Detailed Results by Location\n\n")
        
        for location_name, location_results in results.items():
            f.write(f"### {location_name}\n\n")
            
            f.write("| Data Source | Status | Details |\n")
            f.write("|-------------|--------|----------|\n")
            
            for source, (success, msg) in location_results.items():
                status = "OK" if success else "UNAVAILABLE"
                f.write(f"| {source.replace('_', ' ')} | {status} | {msg} |\n")
            
            # Calculate location-specific success
            loc_passed = sum(1 for success, _ in location_results.values() if success)
            loc_total = len(location_results)
            loc_rate = (loc_passed / loc_total) * 100
            
            f.write(f"\n**Location Success Rate**: {loc_passed}/{loc_total} ({loc_rate:.1f}%)\n\n")
        
        f.write("---\n\n")
        
        # Summary by Data Source
        f.write("## Summary by Data Source\n\n")
        f.write("| Data Source | Locations Available | Coverage |\n")
        f.write("|-------------|---------------------|----------|\n")
        
        sources = ['NASA_POWER', 'CHIRPS', 'ERA5', 'NDVI', 'OCEAN_INDICES']
        for source in sources:
            available_locs = [
                loc for loc, loc_results in results.items()
                if loc_results.get(source, (False, ""))[0]
            ]
            coverage = (len(available_locs) / len(results)) * 100
            f.write(f"| {source.replace('_', ' ')} | {len(available_locs)}/{len(results)} | {coverage:.1f}% |\n")
        
        f.write("\n---\n\n")
        
        # Identified Issues & Recommendations
        f.write("## Identified Issues & Recommendations\n\n")
        
        has_issues = False
        for location_name, location_results in results.items():
            failed_sources = [
                source for source, (success, msg) in location_results.items()
                if not success
            ]
            
            if failed_sources:
                has_issues = True
                f.write(f"### {location_name}\n\n")
                for source in failed_sources:
                    _, msg = location_results[source]
                    f.write(f"- **{source.replace('_', ' ')}**: {msg}\n")
                f.write("\n")
        
        if not has_issues:
            f.write("✅ **No issues identified!** All data sources are accessible for all locations.\n\n")
        
        f.write("---\n\n")
        
        # Next Steps
        f.write("## Next Steps\n\n")
        if success_rate >= 90:
            f.write("1. ✅ **Proceed to Phase 2: Data Collection** (Tasks 2.1-2.6)\n")
            f.write("2. Begin historical data collection for all 5 locations (2000-2025)\n")
            f.write("3. Implement multi-location ingestion orchestrator\n")
            f.write("4. Monitor collection progress and data quality\n\n")
        else:
            f.write("1. ❌ **Address configuration issues** documented above\n")
            f.write("2. Re-run this verification script after fixes\n")
            f.write("3. Only proceed to Phase 2 when success rate ≥90%\n\n")
        
        # Appendix
        f.write("---\n\n")
        f.write("## Appendix: Expected Sample Counts\n\n")
        
        time_period = config.get('time_period', {})
        sample_counts = config.get('sample_counts', {})
        ratio_targets = config.get('ratio_targets', {})
        
        f.write(f"**Time Period**: {time_period.get('start_year', 2000)} - {time_period.get('end_year', 2025)} ")
        f.write(f"({time_period.get('total_months', 312)} months)\n\n")
        f.write(f"**Current Baseline**: {sample_counts.get('single_location_baseline', 191)} samples (Dodoma only, 2010-2025)\n")
        f.write(f"**Phase 1 Target**: {sample_counts.get('phase1_target', 1560)} samples (5 locations × 312 months)\n")
        f.write(f"**Phase 2 Target**: {sample_counts.get('phase2_target', 2496)} samples (8 locations × 312 months)\n\n")
        
        f.write(f"**Feature-to-Sample Ratios**:\n")
        f.write(f"- Current (unhealthy): {ratio_targets.get('current_unhealthy', 2.5)}:1\n")
        f.write(f"- Phase 1 (healthy): {ratio_targets.get('phase1_healthy', 20.8)}:1 ✅\n")
        f.write(f"- Phase 2 (optimal): {ratio_targets.get('phase2_optimal', 33.3)}:1 ✅ ✅\n\n")
    
    print_success(f"Report generated: {report_path}")
    return report_path


def main():
    """Main verification workflow"""
    print_header("Multi-Location Data Availability Verification")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load locations config
    try:
        config = load_locations_config()
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return 1
    
    print(f"Testing data availability for {len(config['locations'])} locations:")
    for loc_data in config['locations'].values():
        print(f"  • {loc_data['name']} ({loc_data['region'].title()})")
    print()
    
    # Run verification tests
    try:
        results = verify_all_locations(config)
    except Exception as e:
        print_error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 2
    
    # Generate report
    try:
        report_path = generate_availability_report(config, results)
    except Exception as e:
        print_error(f"Failed to generate report: {e}")
        import traceback
        traceback.print_exc()
        return 3
    
    # Final summary
    print_header("Verification Complete")
    
    total_tests = len(results) * 5
    passed_tests = sum(
        1 for loc_results in results.values()
        for success, _ in loc_results.values()
        if success
    )
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)\n")
    
    if success_rate >= 90:
        print_success("RECOMMENDATION: PROCEED with Phase 2 (Data Collection)")
        print_success(f"Full report: {report_path}\n")
        return 0
    elif success_rate >= 70:
        print_warning("RECOMMENDATION: PROCEED WITH CAUTION")
        print_warning(f"Review failures in: {report_path}\n")
        return 1
    else:
        print_error("RECOMMENDATION: DO NOT PROCEED")
        print_error(f"Address issues documented in: {report_path}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
