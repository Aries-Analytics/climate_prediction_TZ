"""
Script to recalibrate trigger thresholds based on actual processed data.

This script analyzes the current processed data to find thresholds that achieve
target trigger rates:
- Flood: 5-15% (target 10%)
- Drought: 8-20% (target 12%)
- Crop failure: 3-10% (target 6%)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def analyze_flood_thresholds(df):
    """Analyze rainfall data to find optimal flood thresholds."""
    print("\n=== FLOOD TRIGGER ANALYSIS ===")
    
    # Calculate percentiles for daily rainfall
    daily_percentiles = {
        'p90': df['rainfall_mm'].quantile(0.90),
        'p95': df['rainfall_mm'].quantile(0.95),
        'p97': df['rainfall_mm'].quantile(0.97),
        'p99': df['rainfall_mm'].quantile(0.99),
        'p99.5': df['rainfall_mm'].quantile(0.995),
    }
    
    print("\nDaily Rainfall Percentiles:")
    for p, val in daily_percentiles.items():
        print(f"  {p}: {val:.2f} mm")
    
    # Calculate percentiles for 7-day rainfall
    rainfall_7day_percentiles = {
        'p90': df['rainfall_7day'].quantile(0.90),
        'p95': df['rainfall_7day'].quantile(0.95),
        'p97': df['rainfall_7day'].quantile(0.97),
        'p99': df['rainfall_7day'].quantile(0.99),
        'p99.5': df['rainfall_7day'].quantile(0.995),
    }
    
    print("\n7-Day Rainfall Percentiles:")
    for p, val in rainfall_7day_percentiles.items():
        print(f"  {p}: {val:.2f} mm")
    
    # Test different threshold combinations to achieve 10% trigger rate
    target_rate = 0.10
    print(f"\nTesting thresholds for {target_rate:.0%} target rate...")
    
    # Strategy: Use OR logic - trigger if ANY condition is met
    # Try different combinations
    best_combo = None
    best_diff = float('inf')
    
    for daily_p in [0.95, 0.97, 0.99, 0.995]:
        for weekly_p in [0.95, 0.97, 0.99, 0.995]:
            daily_thresh = df['rainfall_mm'].quantile(daily_p)
            weekly_thresh = df['rainfall_7day'].quantile(weekly_p)
            
            # Simulate trigger
            trigger = (
                (df['rainfall_mm'] > daily_thresh) |
                (df['rainfall_7day'] > weekly_thresh)
            )
            rate = trigger.mean()
            diff = abs(rate - target_rate)
            
            if diff < best_diff:
                best_diff = diff
                best_combo = {
                    'daily_percentile': daily_p,
                    'daily_threshold': daily_thresh,
                    'weekly_percentile': weekly_p,
                    'weekly_threshold': weekly_thresh,
                    'trigger_rate': rate
                }
    
    print(f"\nBest combination:")
    print(f"  Daily: {best_combo['daily_percentile']:.1%} percentile = {best_combo['daily_threshold']:.2f} mm")
    print(f"  Weekly: {best_combo['weekly_percentile']:.1%} percentile = {best_combo['weekly_threshold']:.2f} mm")
    print(f"  Resulting trigger rate: {best_combo['trigger_rate']:.2%}")
    
    return best_combo


def analyze_drought_thresholds(df):
    """Analyze drought indicators to find optimal thresholds."""
    print("\n=== DROUGHT TRIGGER ANALYSIS ===")
    
    # SPI percentiles
    spi_percentiles = {
        'p5': df['spi_30day'].quantile(0.05),
        'p10': df['spi_30day'].quantile(0.10),
        'p12': df['spi_30day'].quantile(0.12),
        'p15': df['spi_30day'].quantile(0.15),
        'p20': df['spi_30day'].quantile(0.20),
    }
    
    print("\nSPI-30 Percentiles:")
    for p, val in spi_percentiles.items():
        print(f"  {p}: {val:.2f}")
    
    # Note: Consecutive dry days is 0 for monthly data
    # Use SPI alone for drought trigger
    
    # Test different SPI thresholds for 12% target rate
    target_rate = 0.12
    print(f"\nTesting SPI thresholds for {target_rate:.0%} target rate...")
    print("(Using SPI alone since this is monthly aggregated data)")
    
    best_combo = None
    best_diff = float('inf')
    
    for spi_p in [0.08, 0.10, 0.12, 0.15, 0.18, 0.20]:
        spi_thresh = df['spi_30day'].quantile(spi_p)
        
        # Simulate trigger (SPI only)
        trigger = (df['spi_30day'] < spi_thresh)
        rate = trigger.mean()
        diff = abs(rate - target_rate)
        
        if diff < best_diff:
            best_diff = diff
            best_combo = {
                'spi_percentile': spi_p,
                'spi_threshold': spi_thresh,
                'dry_days_threshold': 28,  # Keep for config compatibility
                'trigger_rate': rate
            }
    
    print(f"\nBest combination:")
    print(f"  SPI: {best_combo['spi_percentile']:.1%} percentile = {best_combo['spi_threshold']:.2f}")
    print(f"  Resulting trigger rate: {best_combo['trigger_rate']:.2%}")
    print(f"  (Dry days threshold kept at 28 for config compatibility)")
    
    return best_combo


def analyze_crop_failure_thresholds(df):
    """Analyze vegetation data to find optimal crop failure thresholds."""
    print("\n=== CROP FAILURE TRIGGER ANALYSIS ===")
    
    # VCI percentiles (low values indicate stress)
    vci_percentiles = {
        'p5': df['vci'].quantile(0.05),
        'p10': df['vci'].quantile(0.10),
        'p15': df['vci'].quantile(0.15),
        'p20': df['vci'].quantile(0.20),
    }
    
    print("\nVCI Percentiles (low = stress):")
    for p, val in vci_percentiles.items():
        print(f"  {p}: {val:.2f}")
    
    # NDVI anomaly percentiles
    ndvi_anom_percentiles = {
        'p5': df['ndvi_anomaly_std'].quantile(0.05),
        'p10': df['ndvi_anomaly_std'].quantile(0.10),
        'p15': df['ndvi_anomaly_std'].quantile(0.15),
        'p20': df['ndvi_anomaly_std'].quantile(0.20),
    }
    
    print("\nNDVI Anomaly (std) Percentiles:")
    for p, val in ndvi_anom_percentiles.items():
        print(f"  {p}: {val:.2f}")
    
    # Test different threshold combinations for 6% target rate
    target_rate = 0.06
    print(f"\nTesting thresholds for {target_rate:.0%} target rate...")
    
    best_combo = None
    best_diff = float('inf')
    
    for vci_p in [0.05, 0.10, 0.15, 0.20]:
        for ndvi_p in [0.05, 0.10, 0.15, 0.20]:
            vci_thresh = df['vci'].quantile(vci_p)
            ndvi_thresh = df['ndvi_anomaly_std'].quantile(ndvi_p)
            
            # Simulate trigger (OR logic - either condition)
            trigger = (
                (df['vci'] < vci_thresh) |
                (df['ndvi_anomaly_std'] < ndvi_thresh)
            )
            rate = trigger.mean()
            diff = abs(rate - target_rate)
            
            if diff < best_diff:
                best_diff = diff
                best_combo = {
                    'vci_percentile': vci_p,
                    'vci_threshold': vci_thresh,
                    'ndvi_percentile': ndvi_p,
                    'ndvi_threshold': ndvi_thresh,
                    'trigger_rate': rate
                }
    
    print(f"\nBest combination:")
    print(f"  VCI: {best_combo['vci_percentile']:.1%} percentile = {best_combo['vci_threshold']:.2f}")
    print(f"  NDVI anomaly: {best_combo['ndvi_percentile']:.1%} percentile = {best_combo['ndvi_threshold']:.2f} std")
    print(f"  Resulting trigger rate: {best_combo['trigger_rate']:.2%}")
    
    return best_combo


def update_config_file(flood_config, drought_config, crop_config):
    """Update the trigger thresholds configuration file."""
    config_path = Path('configs/trigger_thresholds.yaml')
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update flood triggers
    config['flood_triggers']['daily_rainfall_mm']['threshold'] = round(flood_config['daily_threshold'], 2)
    config['flood_triggers']['rainfall_7day_mm']['threshold'] = round(flood_config['weekly_threshold'], 2)
    
    # Update drought triggers
    config['drought_triggers']['spi_30day']['threshold'] = round(drought_config['spi_threshold'], 2)
    # Use same threshold for both seasons for now
    config['drought_triggers']['consecutive_dry_days']['wet_season_threshold'] = int(drought_config['dry_days_threshold'])
    config['drought_triggers']['consecutive_dry_days']['dry_season_threshold'] = int(drought_config['dry_days_threshold'])
    
    # Update crop failure triggers
    config['crop_failure_triggers']['vci_threshold']['critical'] = round(crop_config['vci_threshold'], 1)
    config['crop_failure_triggers']['ndvi_anomaly_std']['threshold'] = round(crop_config['ndvi_threshold'], 2)
    
    # Update calibration date and data period
    from datetime import datetime
    config['calibration_date'] = datetime.now().strftime('%Y-%m-%d')
    config['data_period'] = '2000-01-01 to 2025-12-31'
    
    # Save updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✓ Updated configuration file: {config_path}")
    print("\nNew thresholds:")
    print(f"  Flood - Daily: {flood_config['daily_threshold']:.2f} mm, 7-day: {flood_config['weekly_threshold']:.2f} mm")
    print(f"  Drought - SPI: {drought_config['spi_threshold']:.2f}, Dry days: {drought_config['dry_days_threshold']:.0f}")
    print(f"  Crop - VCI: {crop_config['vci_threshold']:.1f}, NDVI: {crop_config['ndvi_threshold']:.2f} std")


def main():
    """Main calibration workflow."""
    print("=" * 70)
    print("TRIGGER THRESHOLD RECALIBRATION")
    print("=" * 70)
    
    # Load processed data
    chirps_path = Path('data/processed/chirps_processed.csv')
    ndvi_path = Path('data/processed/ndvi_processed.csv')
    
    if not chirps_path.exists():
        print(f"Error: {chirps_path} not found. Run pipeline first.")
        return
    
    if not ndvi_path.exists():
        print(f"Error: {ndvi_path} not found. Run pipeline first.")
        return
    
    print(f"\nLoading data from:")
    print(f"  - {chirps_path}")
    print(f"  - {ndvi_path}")
    
    chirps_df = pd.read_csv(chirps_path)
    ndvi_df = pd.read_csv(ndvi_path)
    
    print(f"\nData loaded:")
    print(f"  CHIRPS: {len(chirps_df)} records ({chirps_df['year'].min()}-{chirps_df['year'].max()})")
    print(f"  NDVI: {len(ndvi_df)} records ({ndvi_df['year'].min()}-{ndvi_df['year'].max()})")
    
    # Filter to 2000-2025 for better statistical reliability
    print(f"\nFiltering data to 2000-2025 (25 years for robust statistics)...")
    chirps_df = chirps_df[chirps_df['year'] >= 2000].copy()
    ndvi_df = ndvi_df[ndvi_df['year'] >= 2000].copy()
    
    print(f"  CHIRPS filtered: {len(chirps_df)} records ({chirps_df['year'].min()}-{chirps_df['year'].max()})")
    print(f"  NDVI filtered: {len(ndvi_df)} records ({ndvi_df['year'].min()}-{ndvi_df['year'].max()})")
    
    # Analyze and find optimal thresholds
    flood_config = analyze_flood_thresholds(chirps_df)
    drought_config = analyze_drought_thresholds(chirps_df)
    crop_config = analyze_crop_failure_thresholds(ndvi_df)
    
    # Update configuration file
    update_config_file(flood_config, drought_config, crop_config)
    
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review the updated thresholds in configs/trigger_thresholds.yaml")
    print("  2. Rerun processing: python scripts/reprocess_with_new_thresholds.py")
    print("  3. Verify trigger rates with: python -m pytest tests/test_trigger_integration.py")


if __name__ == '__main__':
    main()
