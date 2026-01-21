from app.core.database import SessionLocal
from app.models.climate_forecast import ClimateForecast
from app.models.trigger_alert import TriggerAlert
from datetime import date
from sqlalchemy import func

def inspect_data():
    db = SessionLocal()
    today = date.today()
    print(f"--- Inspecting Data for Target Date >= {today} ---")
    
    # Count Forecasts
    count = db.query(ClimateForecast).filter(ClimateForecast.target_date >= today).count()
    print(f"Total Future Forecasts: {count}")
    
    # Inspect Alerts
    alerts = db.query(TriggerAlert).join(ClimateForecast).filter(
        ClimateForecast.target_date >= today
    ).all()
    
    print(f"Total Future Alerts: {len(alerts)}")
    
    print("\n--- Alert Breakdown by Type ---")
    type_counts = {}
    for a in alerts:
        type_counts[a.alert_type] = type_counts.get(a.alert_type, 0) + 1
    for t, c in type_counts.items():
        print(f"{t}: {c}")
        
    print("\n--- Sample Drought Alerts ---")
    droughts = [a for a in alerts if a.alert_type in ['rainfall_deficit', 'drought']]
    for a in droughts[:5]:
        print(f"ID: {a.id}, Severity: {a.severity}, ForecastID: {a.climate_forecast_id}")
        f = a.climate_forecast
        print(f"  Target: {f.target_date}, Rain: {f.rainfall_mm}mm, Created: {f.created_at}, Model: {f.model_version}")

    print("\n--- Model Versions in Future Forecasts ---")
    versions = db.query(ClimateForecast.model_version, func.count(ClimateForecast.id)).filter(
        ClimateForecast.target_date >= today
    ).group_by(ClimateForecast.model_version).all()
    for v, c in versions:
        print(f"Version '{v}': {c} forecasts")

if __name__ == "__main__":
    inspect_data()
