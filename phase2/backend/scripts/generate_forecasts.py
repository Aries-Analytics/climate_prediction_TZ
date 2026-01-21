#!/usr/bin/env python3
"""
Generate Climate Forecasts & Insurance Triggers (Kilombero Pilot)

This script generates:
1. Rainfall forecasts (ClimateForecast) for the next 3-6 months.
2. Insurance triggers (TriggerAlert) based on Kilombero rice thresholds.

Usage:
  docker compose exec backend python scripts/generate_forecasts.py
"""

import sys
import os
from datetime import date

# Ensure we're in the backend directory for imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# If 'backend' subdirectory exists (local dev), add it too
backend_dir = os.path.join(root_dir, 'backend')
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.services.forecast_service import generate_climate_forecasts_all_locations


def main():
    print("=" * 60)
    print("HEWASENSE CLIMATE FORECAST ENGINE")
    print("   Target: Kilombero Valley Rice Pilot")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        start_date = date.today()
        horizons = [3, 4, 5, 6]
        
        print(f"\nGeneratin forecasts...")
        print(f"   Date: {start_date}")
        print(f"   Horizons: {horizons} months")
        print(f"   Variable: Rainfall (mm)")
        
        forecasts = generate_climate_forecasts_all_locations(
            db=db,
            start_date=start_date,
            horizons=horizons
        )
        
        print(f"\nGenerated {len(forecasts)} climate forecasts")
        
        # Count alerts
        alerts_count = 0
        for f in forecasts:
            alerts_count += len(f.trigger_alerts)
            if f.trigger_alerts:
                print(f"   Location {f.location_id} ({f.target_date}): {len(f.trigger_alerts)} alerts")
                for alert in f.trigger_alerts:
                    print(f"      - {alert.alert_type.upper()} ({alert.severity}): {alert.forecast_value}mm vs {alert.threshold_value}mm")
        
        print("\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"   - Forecasts Created: {len(forecasts)}")
        print(f"   - Active Triggers: {alerts_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
