from app.core.database import SessionLocal
from app.models.forecast import Forecast

db = SessionLocal()
forecasts = db.query(Forecast).all()
print(f'Total forecasts in DB: {len(forecasts)}')
for f in forecasts[:5]:
    print(f'  {f.trigger_type} (horizon={f.horizon_months}): location_id={f.location_id}, date={f.forecast_date}')
