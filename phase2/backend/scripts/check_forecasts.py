"""Quick script to check forecast data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.forecast import Forecast
from sqlalchemy import func

db = SessionLocal()

# Get forecast statistics
print("=" * 60)
print("FORECAST DATA CHECK")
print("=" * 60)

total = db.query(Forecast).count()
print(f"\nTotal forecasts: {total}")

# Group by trigger type
by_type = db.query(
    Forecast.trigger_type, 
    func.count(Forecast.id)
).group_by(Forecast.trigger_type).all()

print("\nBy trigger type:")
for t, c in by_type:
    print(f"  {t}: {c}")

# Check probability distribution
print("\nProbability statistics:")
forecasts = db.query(Forecast).all()
for f in forecasts[:5]:
    print(f"  ID {f.id}: {f.trigger_type}, target={f.target_date}, prob={f.probability:.4f}, CI=[{f.confidence_lower:.4f}, {f.confidence_upper:.4f}]")

# Check for invalid probabilities
invalid = [f for f in forecasts if f.probability < 0 or f.probability > 1]
print(f"\nInvalid probabilities (outside 0-1): {len(invalid)}")

# Check date range
if forecasts:
    dates = sorted([f.target_date for f in forecasts])
    print(f"\nDate range: {dates[0]} to {dates[-1]}")
    
    # Check forecast dates
    forecast_dates = sorted(set([f.forecast_date for f in forecasts]))
    print(f"Forecast generation dates: {forecast_dates}")

db.close()
