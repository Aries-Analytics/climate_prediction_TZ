
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

# Need to make sure backend/app is importable
# Assuming running from 'phase2' directory
if 'backend' not in sys.path:
    sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.app.core.database import SessionLocal
    from backend.app.models.climate_forecast import ClimateForecast
    from backend.app.models.forecast import Forecast
    from backend.app.models.location import Location
except ImportError as e:
    print(f"Import Error: {e}")
    # Try different path structure if above fails
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from app.core.database import SessionLocal
    from app.models.climate_forecast import ClimateForecast
    from app.models.forecast import Forecast
    from app.models.location import Location

def check_data():
    try:
        db = SessionLocal()
        
        loc_count = db.query(Location).count()
        print(f"Locations count: {loc_count}")
        
        cf_count = db.query(ClimateForecast).count()
        print(f"ClimateForecasts count: {cf_count}")
        
        if loc_count > 0:
            first_loc = db.query(Location).first()
            cf_loc_count = db.query(ClimateForecast).filter(ClimateForecast.location_id == first_loc.id).count()
            print(f"ClimateForecasts for Location {first_loc.id} ({first_loc.name}): {cf_loc_count}")
        
        f_count = db.query(Forecast).count()
        print(f"Forecasts count: {f_count}")
        
        db.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    check_data()
