#!/usr/bin/env python3
"""
Generate forecasts for Early Warning Dashboard

This script generates forecasts using the forecast service and populates
recommendations for high-risk predictions.

Usage (from container):
  docker exec climate_backend_dev python -c "from scripts.generate_forecasts import main; main()"
  
Or manually from backend directory:
  cd backend && python -c "import sys; sys.path.insert(0, '..'); from scripts.generate_forecasts import main; main()"
"""

import sys
import os

# Ensure we're in the backend directory for imports
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from datetime import date
from app.core.database import SessionLocal
from app.services.forecast_service import generate_forecasts_all_locations, generate_all_recommendations


def main():
    """Generate forecasts and recommendations"""
    print("=" * 60)
    print("GENERATING FORECASTS FOR ALL 6 LOCATIONS")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Generate forecasts for all locations with 3-6 month horizons
        print("\n📊 Generating forecasts for all locations...")
        print(f"   Forecast date: {date.today()}")
        print(f"   Horizons: 3, 4, 5, 6 months")
        print(f"   Trigger types: Drought, Flood, Crop Failure")
        print(f"   Generating for ALL locations in database...\n")
        
        forecasts = generate_forecasts_all_locations(
            db=db,
            start_date=date.today(),
            horizons=[3, 4, 5, 6]
        )
        
        print(f"\n✅ Generated {len(forecasts)} forecasts")
        
        # Show forecast summary
        for i, f in enumerate(forecasts, 1):
            print(f"   {i}. {f.trigger_type} ({f.horizon_months}mo): {f.probability:.1%} probability")
        
        # Generate recommendations for high-risk forecasts
        print(f"\n📋 Generating recommendations (threshold: >30% probability)...")
        recommendations = generate_all_recommendations(db, min_probability=0.3)
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. Priority: {rec.priority.upper()} - {rec.recommendation_text[:60]}...")
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\n✅ Database updated with:")
        print(f"   - {len(forecasts)} forecasts")
        print(f"   - {len(recommendations)} recommendations")
        print("\n💡 Next steps:")
        print("   1. Refresh the Early Warning dashboard")
        print("   2. View forecasts at http://localhost:3000")
        print("   3. Check recommendations panel")
        
    except Exception as e:
        print(f"\n❌ Error generating forecasts: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
