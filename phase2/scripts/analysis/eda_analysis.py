"""
Exploratory Data Analysis (EDA) for Tanzania Climate Data Pipeline
Analyzes the master dataset created from all data sources
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Load the master dataset
data_path = Path("outputs/processed/master_dataset.csv")
df = pd.read_csv(data_path)

print("="*80)
print("TANZANIA CLIMATE DATA - EXPLORATORY DATA ANALYSIS")
print("="*80)

# === BASIC INFORMATION ===
print("\n1. DATASET OVERVIEW")
print("-" * 80)
print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"Date range: {df['year'].min()}-{df['month'].min():02d} to {df['year'].max()}-{df['month'].max():02d}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# === DATA SOURCES ===
print("\n2. DATA SOURCES")
print("-" * 80)
if 'data_source_left' in df.columns:
    print(f"CHIRPS source: {df['data_source_left'].iloc[0]}")
if 'data_source_right' in df.columns:
    print(f"NDVI source: {df['data_source_right'].iloc[0]}")

# === KEY VARIABLES SUMMARY ===
print("\n3. KEY CLIMATE VARIABLES SUMMARY")
print("-" * 80)

key_vars = {
    'Temperature (°C)': 'temp_mean_c',
    'Rainfall (mm)': 'rainfall_mm',
    'NDVI': 'ndvi',
    'ONI (ENSO)': 'oni',
    'IOD': 'iod',
    'Humidity (%)': 'humidity_pct',
    'Solar Radiation (W/m²)': 'solar_rad_wm2'
}

summary_stats = []
for name, col in key_vars.items():
    if col in df.columns:
        stats = df[col].describe()
        summary_stats.append({
            'Variable': name,
            'Mean': f"{stats['mean']:.2f}",
            'Std': f"{stats['std']:.2f}",
            'Min': f"{stats['min']:.2f}",
            'Max': f"{stats['max']:.2f}",
            'Missing': df[col].isna().sum()
        })

summary_df = pd.DataFrame(summary_stats)
print(summary_df.to_string(index=False))

# === ENSO PHASE DISTRIBUTION ===
print("\n4. ENSO PHASE DISTRIBUTION")
print("-" * 80)
if 'enso_phase' in df.columns:
    phase_counts = df['enso_phase'].value_counts()
    print(phase_counts)
    print(f"\nDominant phase: {phase_counts.index[0]} ({phase_counts.iloc[0]/len(df)*100:.1f}%)")

# === SEASONAL PATTERNS ===
print("\n5. SEASONAL PATTERNS")
print("-" * 80)

# Rainfall by month
if 'rainfall_mm' in df.columns:
    monthly_rainfall = df.groupby('month')['rainfall_mm'].mean()
    print("\nAverage Rainfall by Month:")
    for month, rainfall in monthly_rainfall.items():
        month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month-1]
        print(f"  {month_name}: {rainfall:6.2f} mm")
    
    # Identify rainy seasons
    wet_months = monthly_rainfall[monthly_rainfall > monthly_rainfall.mean()].index.tolist()
    print(f"\nWet months (above average): {', '.join([str(m) for m in wet_months])}")

# === DROUGHT AND FLOOD INDICATORS ===
print("\n6. DROUGHT AND FLOOD INDICATORS")
print("-" * 80)

if 'is_drought_month' in df.columns:
    drought_months = df['is_drought_month'].sum()
    print(f"Drought months detected: {drought_months} ({drought_months/len(df)*100:.1f}%)")

if 'drought_trigger' in df.columns:
    drought_triggers = df['drought_trigger'].sum()
    print(f"Drought insurance triggers: {drought_triggers}")

if 'flood_trigger' in df.columns:
    flood_triggers = df['flood_trigger'].sum()
    print(f"Flood insurance triggers: {flood_triggers}")

if 'crop_failure_trigger' in df.columns:
    crop_triggers = df['crop_failure_trigger'].sum()
    print(f"Crop failure triggers: {crop_triggers}")

# === VEGETATION HEALTH ===
print("\n7. VEGETATION HEALTH (NDVI)")
print("-" * 80)

if 'ndvi' in df.columns:
    print(f"Mean NDVI: {df['ndvi'].mean():.3f}")
    print(f"NDVI range: {df['ndvi'].min():.3f} to {df['ndvi'].max():.3f}")
    
    if 'vci' in df.columns:
        print(f"\nVegetation Condition Index (VCI):")
        print(f"  Mean: {df['vci'].mean():.1f}")
        
        if 'vci_class' in df.columns:
            vci_dist = df['vci_class'].value_counts()
            print(f"\nVCI Classification:")
            for cls, count in vci_dist.items():
                print(f"  {cls}: {count} months ({count/len(df)*100:.1f}%)")

# === CORRELATIONS ===
print("\n8. KEY CORRELATIONS")
print("-" * 80)

corr_vars = ['temp_mean_c', 'rainfall_mm', 'ndvi', 'oni', 'iod', 'humidity_pct']
available_vars = [v for v in corr_vars if v in df.columns]

if len(available_vars) >= 2:
    corr_matrix = df[available_vars].corr()
    print("\nCorrelation Matrix:")
    print(corr_matrix.round(3))
    
    # Highlight strong correlations
    print("\nStrong correlations (|r| > 0.5):")
    for i in range(len(available_vars)):
        for j in range(i+1, len(available_vars)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > 0.5:
                print(f"  {available_vars[i]} ↔ {available_vars[j]}: {corr_val:.3f}")

# === CLIMATE IMPACTS ===
print("\n9. CLIMATE IMPACTS ON RAINFALL")
print("-" * 80)

if all(col in df.columns for col in ['rainfall_mm', 'enso_phase']):
    rainfall_by_enso = df.groupby('enso_phase')['rainfall_mm'].agg(['mean', 'std', 'count'])
    print("\nRainfall by ENSO Phase:")
    print(rainfall_by_enso.round(2))

if all(col in df.columns for col in ['rainfall_mm', 'iod']):
    # Classify IOD
    df['iod_phase'] = pd.cut(df['iod'], bins=[-np.inf, -0.4, 0.4, np.inf], 
                              labels=['Negative', 'Neutral', 'Positive'])
    rainfall_by_iod = df.groupby('iod_phase')['rainfall_mm'].agg(['mean', 'std', 'count'])
    print("\nRainfall by IOD Phase:")
    print(rainfall_by_iod.round(2))

# === DATA QUALITY ===
print("\n10. DATA QUALITY ASSESSMENT")
print("-" * 80)

missing_summary = df.isnull().sum()
missing_pct = (missing_summary / len(df) * 100).round(2)
missing_df = pd.DataFrame({
    'Column': missing_summary.index,
    'Missing': missing_summary.values,
    'Percent': missing_pct.values
})
missing_df = missing_df[missing_df['Missing'] > 0].sort_values('Missing', ascending=False)

if len(missing_df) > 0:
    print(f"\nColumns with missing values ({len(missing_df)} total):")
    print(missing_df.head(10).to_string(index=False))
else:
    print("\n✓ No missing values detected!")

# === EXTREME EVENTS ===
print("\n11. EXTREME EVENTS DETECTED")
print("-" * 80)

if 'rainfall_mm' in df.columns:
    # Extreme rainfall
    extreme_rain = df[df['rainfall_mm'] > df['rainfall_mm'].quantile(0.95)]
    print(f"\nExtreme rainfall events (>95th percentile):")
    print(f"  Count: {len(extreme_rain)}")
    if len(extreme_rain) > 0:
        print(f"  Max: {extreme_rain['rainfall_mm'].max():.2f} mm in {extreme_rain.loc[extreme_rain['rainfall_mm'].idxmax(), 'year']}-{extreme_rain.loc[extreme_rain['rainfall_mm'].idxmax(), 'month']:02d}")
    
    # Drought events
    drought_rain = df[df['rainfall_mm'] < df['rainfall_mm'].quantile(0.05)]
    print(f"\nDrought events (rainfall <5th percentile):")
    print(f"  Count: {len(drought_rain)}")
    if len(drought_rain) > 0:
        print(f"  Min: {drought_rain['rainfall_mm'].min():.2f} mm in {drought_rain.loc[drought_rain['rainfall_mm'].idxmin(), 'year']}-{drought_rain.loc[drought_rain['rainfall_mm'].idxmin(), 'month']:02d}")

if 'temp_mean_c' in df.columns:
    # Heat waves
    hot_months = df[df['temp_mean_c'] > df['temp_mean_c'].quantile(0.95)]
    print(f"\nHeat events (>95th percentile):")
    print(f"  Count: {len(hot_months)}")
    if len(hot_months) > 0:
        print(f"  Max: {hot_months['temp_mean_c'].max():.2f}°C in {hot_months.loc[hot_months['temp_mean_c'].idxmax(), 'year']}-{hot_months.loc[hot_months['temp_mean_c'].idxmax(), 'month']:02d}")

print("\n" + "="*80)
print("EDA COMPLETE")
print("="*80)
print(f"\nDataset saved at: {data_path}")
print("Ready for modeling and further analysis!")
