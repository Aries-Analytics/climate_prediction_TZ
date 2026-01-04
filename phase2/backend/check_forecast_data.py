from app.core.database import SessionLocal
from app.models.forecast import Forecast
from sqlalchemy import func

db = SessionLocal()

total = db.query(func.count(Forecast.id)).scalar()
dates = db.query(func.count(func.distinct(Forecast.forecast_date))).scalar()

print(f'Total forecasts: {total}')
print(f'Unique forecast dates: {dates}')
print('\nForecast dates:')
for d in db.query(func.distinct(Forecast.forecast_date)).order_by(Forecast.forecast_date).all():
    count = db.query(func.count(Forecast.id)).filter(Forecast.forecast_date == d[0]).scalar()
    print(f'  {d[0]}: {count} forecasts')

db.close()
