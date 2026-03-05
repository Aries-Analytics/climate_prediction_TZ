"""
Backfill atmospheric data from raw CSV files into ClimateData table.

This script reads the existing raw CSV files from data/raw/ and updates
ClimateData records with atmospheric fields that were previously fetched
from NASA POWER and ERA5 APIs but not stored in the database.

Usage:
    cd phase2
    python scripts/backfill_atmospheric_data.py
"""

import math
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pandas as pd
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from backend.app.models.climate_data import ClimateData


def get_db_session():
    """Get database session from environment or default."""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hewasense')
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def backfill_nasa_power(db, data_dir):
    """Backfill rel_humidity_pct and solar_rad_wm2 from nasa_power_raw.csv."""
    csv_path = os.path.join(data_dir, 'raw', 'nasa_power_raw.csv')
    if not os.path.exists(csv_path):
        print(f"  SKIP: {csv_path} not found")
        return 0

    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} records from nasa_power_raw.csv")

    updated = 0
    for _, row in df.iterrows():
        # Build date from year/month
        try:
            record_date = pd.Timestamp(year=int(row['year']), month=int(row['month']), day=1).date()
        except (ValueError, KeyError):
            continue

        lat = float(row.get('latitude', -6.369028))
        lon = float(row.get('longitude', 34.888822))

        existing = (
            db.query(ClimateData)
            .filter(
                and_(
                    ClimateData.date == record_date,
                    ClimateData.location_lat >= lat - 0.01,
                    ClimateData.location_lat <= lat + 0.01,
                    ClimateData.location_lon >= lon - 0.01,
                    ClimateData.location_lon <= lon + 0.01,
                )
            )
            .first()
        )

        if existing:
            changed = False
            if 'rh2m' in row and pd.notna(row['rh2m']) and existing.rel_humidity_pct is None:
                existing.rel_humidity_pct = float(row['rh2m'])
                changed = True
            if 'allsky_sfc_sw_dwn' in row and pd.notna(row['allsky_sfc_sw_dwn']) and existing.solar_rad_wm2 is None:
                existing.solar_rad_wm2 = float(row['allsky_sfc_sw_dwn'])
                changed = True
            if changed:
                updated += 1

    db.commit()
    print(f"  Updated {updated} records with NASA POWER atmospheric data")
    return updated


def backfill_era5(db, data_dir):
    """Backfill dewpoint_2m, surface_pressure, wind fields from era5_raw.csv."""
    csv_path = os.path.join(data_dir, 'raw', 'era5_raw.csv')
    if not os.path.exists(csv_path):
        print(f"  SKIP: {csv_path} not found")
        return 0

    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} records from era5_raw.csv")

    # ERA5 column mapping (may already be renamed or still raw)
    col_map = {
        'd2m': 'dewpoint_2m', 'dewpoint_2m': 'dewpoint_2m',
        'sp': 'surface_pressure', 'surface_pressure': 'surface_pressure',
        'u10': 'wind_u_10m', 'wind_u_10m': 'wind_u_10m',
        'v10': 'wind_v_10m', 'wind_v_10m': 'wind_v_10m',
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    tanzania_lat = -6.369028
    tanzania_lon = 34.888822

    updated = 0
    for _, row in df.iterrows():
        try:
            record_date = pd.Timestamp(year=int(row['year']), month=int(row['month']), day=1).date()
        except (ValueError, KeyError):
            continue

        existing = (
            db.query(ClimateData)
            .filter(
                and_(
                    ClimateData.date == record_date,
                    ClimateData.location_lat >= tanzania_lat - 0.01,
                    ClimateData.location_lat <= tanzania_lat + 0.01,
                    ClimateData.location_lon >= tanzania_lon - 0.01,
                    ClimateData.location_lon <= tanzania_lon + 0.01,
                )
            )
            .first()
        )

        if existing:
            changed = False
            # ERA5 temp values are in Kelvin — convert to Celsius
            if 'dewpoint_2m' in row and pd.notna(row['dewpoint_2m']) and existing.dewpoint_2m is None:
                val = float(row['dewpoint_2m'])
                existing.dewpoint_2m = val - 273.15 if val > 100 else val  # Kelvin check
                changed = True
            if 'surface_pressure' in row and pd.notna(row['surface_pressure']) and existing.surface_pressure is None:
                existing.surface_pressure = float(row['surface_pressure'])
                changed = True
            if 'wind_u_10m' in row and pd.notna(row['wind_u_10m']) and existing.wind_u_10m is None:
                existing.wind_u_10m = float(row['wind_u_10m'])
                changed = True
            if 'wind_v_10m' in row and pd.notna(row['wind_v_10m']) and existing.wind_v_10m is None:
                existing.wind_v_10m = float(row['wind_v_10m'])
                changed = True

            # Derive wind speed and direction
            if existing.wind_u_10m is not None and existing.wind_v_10m is not None:
                u, v = float(existing.wind_u_10m), float(existing.wind_v_10m)
                existing.wind_speed_ms = math.sqrt(u**2 + v**2)
                existing.wind_direction_deg = (math.degrees(math.atan2(-u, -v)) + 360) % 360
                changed = True

            if changed:
                updated += 1

    db.commit()
    print(f"  Updated {updated} records with ERA5 atmospheric data")
    return updated


def main():
    print("=" * 60)
    print("Backfilling atmospheric data from raw CSVs")
    print("=" * 60)

    db = get_db_session()

    # Determine data directory
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data')

    print(f"\nData directory: {os.path.abspath(data_dir)}")

    print("\n--- NASA POWER Backfill ---")
    nasa_count = backfill_nasa_power(db, data_dir)

    print("\n--- ERA5 Backfill ---")
    era5_count = backfill_era5(db, data_dir)

    print(f"\n{'=' * 60}")
    print(f"Total records updated: {nasa_count + era5_count}")

    # Verify: count records with atmospheric data
    with_humidity = db.query(ClimateData).filter(ClimateData.rel_humidity_pct.isnot(None)).count()
    with_solar = db.query(ClimateData).filter(ClimateData.solar_rad_wm2.isnot(None)).count()
    with_wind = db.query(ClimateData).filter(ClimateData.wind_speed_ms.isnot(None)).count()
    with_pressure = db.query(ClimateData).filter(ClimateData.surface_pressure.isnot(None)).count()

    print(f"\nVerification counts:")
    print(f"  Records with humidity:  {with_humidity}")
    print(f"  Records with solar:     {with_solar}")
    print(f"  Records with wind:      {with_wind}")
    print(f"  Records with pressure:  {with_pressure}")

    db.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
