"""
Fetch Daily Climate Data (NASA POWER) - 2015-2025
=================================================

Fetches daily Rainfall, Temperature, and Soil Moisture for 6 Tanzania locations.
Source: NASA POWER API (Free, No Key)
Parameters:
- PRECTOTCORR: Corrected Precipitation (mm/day)
- T2M: Temperature at 2 Meters (C)
- GWETPROF: Profile Soil Moisture (0-1 fraction)

Output: outputs/raw/daily_climate_data_2015_2025.csv
"""

import pandas as pd
import requests
import time
import os
from datetime import datetime

# 1. Configuration
LOCATIONS = {
    'Arusha': {'lat': -3.37, 'lon': 36.68},
    'Dodoma': {'lat': -6.16, 'lon': 35.75},
    'Dar es Salaam': {'lat': -6.79, 'lon': 39.28},
    'Mbeya': {'lat': -8.90, 'lon': 33.46},
    'Morogoro': {'lat': -6.82, 'lon': 37.66},
    'Mwanza': {'lat': -2.51, 'lon': 32.90}
}

START_DATE = "20150101"
END_DATE = "20251231"
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

OUTPUT_DIR = "outputs/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "daily_climate_data_2015_2025.csv")

def fetch_location_data(name, coords):
    """Fetch data for a single location"""
    print(f"Fetching data for {name} ({coords['lat']}, {coords['lon']})...")
    
    params = {
        'parameters': 'PRECTOTCORR,T2M,GWETPROF',
        'community': 'AG',
        'longitude': coords['lon'],
        'latitude': coords['lat'],
        'start': START_DATE,
        'end': END_DATE,
        'format': 'JSON'
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Parse JSON structure
        # properties -> parameter -> {date: value}
        if 'properties' not in data or 'parameter' not in data['properties']:
            print(f"Error: Invalid response format for {name}")
            return pd.DataFrame()
            
        params_data = data['properties']['parameter']
        
        # Convert to DataFrame
        precip = pd.Series(params_data.get('PRECTOTCORR', {}), name='rainfall_mm')
        temp = pd.Series(params_data.get('T2M', {}), name='temp_avg_c')
        moisture = pd.Series(params_data.get('GWETPROF', {}), name='soil_moisture_index')
        
        df = pd.concat([precip, temp, moisture], axis=1)
        df.index.name = 'date_str'
        df = df.reset_index()
        
        # Clean data
        df['date'] = pd.to_datetime(df['date_str'], format='%Y%m%d')
        df['location'] = name
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        
        # Handle NASA fill values (-999)
        df = df.replace(-999, float('nan'))
        df = df.replace(-999.0, float('nan'))
        
        # Interpolate small gaps
        df = df.interpolate(method='linear', limit=3)
        
        print(f"Fetched {len(df)} records for {name}")
        return df[['date', 'location', 'year', 'month', 'day', 'rainfall_mm', 'temp_avg_c', 'soil_moisture_index']]
        
    except Exception as e:
        print(f"Failed to fetch {name}: {str(e)}")
        return pd.DataFrame()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_data = []
    
    print("Starting NASA POWER Daily Data Fetch (2015-2025)")
    print("=" * 60)
    
    for name, coords in LOCATIONS.items():
        df = fetch_location_data(name, coords)
        if not df.empty:
            all_data.append(df)
        time.sleep(1)  # Respect API rate limits
        
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        print("=" * 60)
        print(f"✓ SUCCESSFULLY SAVED: {OUTPUT_FILE}")
        print(f"Total Records: {len(final_df)}")
        print(f"Years Covered: {final_df['year'].min()} - {final_df['year'].max()}")
        print(f"Locations: {final_df['location'].unique()}")
    else:
        print("x NO DATA FETCHED")

if __name__ == "__main__":
    main()
