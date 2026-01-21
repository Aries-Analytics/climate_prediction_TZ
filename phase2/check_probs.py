import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.forecast import Forecast
from sqlalchemy import func

db = SessionLocal()
try:
    # Get distribution of probabilities
    print("Probability Distribution:")
    stats = db.query(
        Forecast.trigger_type,
        func.count(Forecast.id),
        func.min(Forecast.probability),
        func.avg(Forecast.probability),
        func.max(Forecast.probability)
    ).group_by(Forecast.trigger_type).all()
    
    for s in stats:
        print(f"Trigger: {s[0]}, Count: {s[1]}, Min: {s[2]}, Avg: {s[3]}, Max: {s[4]}")

    # Check how many would be filtered at different thresholds
    total = db.query(Forecast).count()
    for thresh in [0.4, 0.5, 0.6, 0.7, 0.8]:
        count = db.query(Forecast).filter(Forecast.probability >= thresh).count()
        print(f"Forecasts >= {thresh}: {count} ({count/total*100:.1f}%)")

except Exception as e:
    print(e)
finally:
    db.close()
