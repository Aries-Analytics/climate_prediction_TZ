from app.core.database import SessionLocal
from app.models.model_metric import ModelMetric
from app.models.climate_data import ClimateData

db = SessionLocal()

print("=" * 60)
print("MODEL METRICS IN DATABASE")
print("=" * 60)
models = db.query(ModelMetric).all()
if models:
    for m in models:
        print(f"\nModel: {m.model_name}")
        print(f"  R2 Score: {m.r2_score}")
        print(f"  RMSE: {m.rmse}")
        print(f"  MAE: {m.mae}")
        print(f"  MAPE: {m.mape}")
        print(f"  Training Date: {m.training_date}")
else:
    print("No models found in database")

print("\n" + "=" * 60)
print("CLIMATE DATA SAMPLE")
print("=" * 60)
climate = db.query(ClimateData).limit(5).all()
for c in climate:
    print(f"\nDate: {c.date}")
    print(f"  NDVI: {c.ndvi}")
    print(f"  ENSO: {c.enso_index}")
    print(f"  IOD: {c.iod_index}")
    print(f"  Temp: {c.temperature_avg}")
    print(f"  Rainfall: {c.rainfall_mm}")

db.close()
