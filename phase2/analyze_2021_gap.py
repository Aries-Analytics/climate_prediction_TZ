"""Analyze the June-September 2021 trigger gap"""
import pandas as pd
import numpy as np

# Load master dataset
df = pd.read_csv('outputs/processed/master_dataset.csv')
df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))

# Filter to June-Sept 2021
df_2021 = df[(df['date'] >= '2021-06-01') & (df['date'] <= '2021-09-30')].copy()

print("=== JUNE-SEPT 2021 ANALYSIS ===")
print(f"Records: {len(df_2021)}\n")

# Check trigger columns
trigger_cols = [c for c in df_2021.columns if 'trigger' in c.lower()]
print("Trigger columns found:", trigger_cols)
print("\nTrigger summary:")
for col in trigger_cols:
    if col in df_2021.columns:
        count = df_2021[col].sum() if df_2021[col].dtype in ['int64', 'float64', 'bool'] else 'N/A'
        print(f"  {col}: {count}")

# Check rainfall and drought indicators
print("\n=== RAINFALL & DROUGHT INDICATORS ===")
if 'rainfall_mm' in df_2021.columns:
    print(f"Rainfall (mm):")
    print(f"  Mean: {df_2021['rainfall_mm'].mean():.2f}")
    print(f"  Min: {df_2021['rainfall_mm'].min():.2f}")
    print(f"  Max: {df_2021['rainfall_mm'].max():.2f}")
    print(f"  Days < 1mm: {(df_2021['rainfall_mm'] < 1).sum()}")

if 'spi_30day' in df_2021.columns:
    print(f"\nSPI-30 day:")
    print(f"  Mean: {df_2021['spi_30day'].mean():.2f}")
    print(f"  Min: {df_2021['spi_30day'].min():.2f}")
    print(f"  Max: {df_2021['spi_30day'].max():.2f}")
    print(f"  Days < -1.5 (drought threshold): {(df_2021['spi_30day'] < -1.5).sum()}")
    print(f"  Days < -0.4 (calibrated threshold): {(df_2021['spi_30day'] < -0.4).sum()}")

if 'consecutive_dry_days' in df_2021.columns:
    print(f"\nConsecutive dry days:")
    print(f"  Mean: {df_2021['consecutive_dry_days'].mean():.2f}")
    print(f"  Max: {df_2021['consecutive_dry_days'].max():.2f}")
    print(f"  Days >= 28 (threshold): {(df_2021['consecutive_dry_days'] >= 28).sum()}")

# Detailed view
print("\n=== DETAILED DATA ===")
cols_to_show = ['date', 'rainfall_mm', 'spi_30day', 'consecutive_dry_days']
if 'drought_trigger' in df_2021.columns:
    cols_to_show.append('drought_trigger')
if 'flood_trigger' in df_2021.columns:
    cols_to_show.append('flood_trigger')

available_cols = [c for c in cols_to_show if c in df_2021.columns]
print(df_2021[available_cols].to_string())

# Compare with 2018 (known drought year)
print("\n\n=== COMPARISON WITH 2018 (KNOWN DROUGHT) ===")
df_2018 = df[(df['date'] >= '2018-06-01') & (df['date'] <= '2018-09-30')].copy()
print(f"2018 June-Sept records: {len(df_2018)}")

if 'rainfall_mm' in df_2018.columns:
    print(f"\n2018 Rainfall (mm):")
    print(f"  Mean: {df_2018['rainfall_mm'].mean():.2f}")
    print(f"  Min: {df_2018['rainfall_mm'].min():.2f}")

if 'spi_30day' in df_2018.columns:
    print(f"\n2018 SPI-30:")
    print(f"  Mean: {df_2018['spi_30day'].mean():.2f}")
    print(f"  Min: {df_2018['spi_30day'].min():.2f}")
    print(f"  Days < -0.4: {(df_2018['spi_30day'] < -0.4).sum()}")

if 'drought_trigger' in df_2018.columns:
    print(f"\n2018 Drought triggers: {df_2018['drought_trigger'].sum()}")

print("\n=== COMPARISON SUMMARY ===")
print(f"2021 Jun-Sep avg rainfall: {df_2021['rainfall_mm'].mean():.2f} mm")
print(f"2018 Jun-Sep avg rainfall: {df_2018['rainfall_mm'].mean():.2f} mm")
print(f"2021 Jun-Sep avg SPI: {df_2021['spi_30day'].mean():.2f}")
print(f"2018 Jun-Sep avg SPI: {df_2018['spi_30day'].mean():.2f}")
