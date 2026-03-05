import pandas as pd
import numpy as np
import os
import sys

# Add project paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app.services.phase_based_coverage import PhaseBasedCoverageService

def analyze_fallback():
    data_path = 'c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/outputs/raw/daily_climate_data_2015_2025.csv'
    
    # We create a 2000-2025 dataset
    # 2015-2025 is actual
    # 2000-2014 is shifted
    
    df_actual = pd.read_csv(data_path)
    df_actual['date'] = pd.to_datetime(df_actual['date'])
    df_actual = df_actual[df_actual['location'] == 'Morogoro'].copy()
    
    df_shifted = pd.read_csv(data_path)
    df_shifted['date'] = pd.to_datetime(df_shifted['date']) - pd.DateOffset(years=15)
    df_shifted = df_shifted[df_shifted['location'] == 'Morogoro'].copy()
    
    df_combined = pd.concat([df_shifted, df_actual]).sort_values('date').reset_index(drop=True)
    
    service = PhaseBasedCoverageService()
    fallback_count = 0
    total_years = 0
    
    for year in range(2000, 2026):
        start_date, triggered, reason = service.calculate_dynamic_start("Morogoro", year, df_combined)
        total_years += 1
        if not triggered:
            fallback_count += 1
            print(f"Year {year}: FALLBACK - {reason}")
        else:
            print(f"Year {year}: DYNAMIC  - {reason}")
            
    freq = (fallback_count / total_years) * 100
    print("-" * 40)
    print(f"Total Years: {total_years}")
    print(f"Fallback Activations: {fallback_count}")
    print(f"Fallback Frequency: {freq:.1f}%")

if __name__ == '__main__':
    analyze_fallback()
