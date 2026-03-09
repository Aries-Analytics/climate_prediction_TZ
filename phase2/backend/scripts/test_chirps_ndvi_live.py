"""
Live CHIRPS + NDVI fetch test — runs locally or inside the backend container.

Tests:
  1. GEE authentication
  2. CHIRPS fetch (full 2024 year) — real GEE data or cached CSV
  3. NDVI fetch (full 2024 year) — real GEE data or cached CSV
  4. DB write + coordinate read-back at Morogoro coords (-6.8211, 37.6595)
  5. Forecast feature prep (can the forecast service find the data?)

Run locally:
  cd backend
  python scripts/test_chirps_ndvi_live.py

Run on server inside container:
  docker exec climate_backend_dev python scripts/test_chirps_ndvi_live.py
"""
import sys
import os
from pathlib import Path

# Path setup: works both locally (from backend/) and inside container (/app/)
backend_dir = Path(__file__).resolve().parent.parent   # .../phase2/backend
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / 'app'))

# Force UTF-8 output on Windows to handle any non-ASCII log messages
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OK  = "[OK]"
ERR = "[FAIL]"
WARN= "[WARN]"

gee_ok = False
chirps_ok = False
ndvi_ok = False

# ── 1. GEE auth ──────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 1: GEE Authentication")
print("="*60)
try:
    import ee

    gee_initialized = False

    # 1a. Service account (Docker/server path)
    sa_email = os.getenv("GEE_SERVICE_ACCOUNT")
    sa_key   = os.getenv("GEE_PRIVATE_KEY_FILE", "/app/secrets/gee-service-account.json")
    if sa_email and os.path.exists(sa_key):
        try:
            credentials = ee.ServiceAccountCredentials(sa_email, sa_key)
            ee.Initialize(credentials)
            gee_initialized = True
            print(f"{OK} GEE authenticated via SERVICE ACCOUNT ({sa_email})")
        except Exception as e:
            print(f"{WARN} Service account auth failed: {e}  -- trying user credentials")

    # 1b. User credentials (local dev / container with cached creds)
    if not gee_initialized:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
        try:
            ee.Initialize(project=project_id)
            gee_initialized = True
            print(f"{OK} GEE authenticated via USER CREDENTIALS (project={project_id})")
        except Exception as e:
            print(f"{ERR} GEE user credential auth failed: {e}")

    gee_ok = gee_initialized

except ImportError:
    print(f"{ERR} earthengine-api not installed")

# ── 2. CHIRPS fetch ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 2: CHIRPS fetch (year 2024)")
print("="*60)
try:
    from modules.ingestion.chirps_ingestion import fetch_chirps_data

    df_chirps = fetch_chirps_data(start_year=2024, end_year=2024, dry_run=False)

    if df_chirps is None or df_chirps.empty:
        print(f"{WARN} CHIRPS returned EMPTY DataFrame (no GEE data and no cache)")
        chirps_ok = False
    else:
        src = df_chirps['data_source'].iloc[0]
        print(f"{OK} CHIRPS fetched {len(df_chirps)} rows  |  data_source={src}")
        latest = df_chirps.sort_values(['year','month']).iloc[-1]
        print(f"   Latest row: {int(latest['year'])}-{int(latest['month']):02d}  "
              f"rainfall_mm={float(latest['rainfall_mm']):.2f}")
        chirps_ok = True

except Exception as e:
    print(f"{ERR} CHIRPS fetch error: {e}")
    import traceback; traceback.print_exc()
    chirps_ok = False

# ── 3. NDVI fetch ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 3: NDVI fetch (year 2024)")
print("="*60)
try:
    from modules.ingestion.ndvi_ingestion import fetch_ndvi_data

    df_ndvi = fetch_ndvi_data(start_year=2024, end_year=2024, dry_run=False)

    if df_ndvi is None or df_ndvi.empty:
        print(f"{WARN} NDVI returned EMPTY DataFrame")
        ndvi_ok = False
    else:
        src = df_ndvi['data_source'].iloc[0]
        print(f"{OK} NDVI fetched {len(df_ndvi)} rows  |  data_source={src}")
        latest = df_ndvi.sort_values(['year','month']).iloc[-1]
        print(f"   Latest row: {int(latest['year'])}-{int(latest['month']):02d}  "
              f"ndvi={float(latest['ndvi']):.4f}")
        ndvi_ok = True

except RuntimeError as e:
    print(f"{WARN} NDVI RuntimeError (GEE unavailable + no cache): {e}")
    ndvi_ok = False
except Exception as e:
    print(f"{ERR} NDVI fetch error: {e}")
    import traceback; traceback.print_exc()
    ndvi_ok = False

# ── 4. DB check ───────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 4: DB check -- Morogoro records at (-6.8211, 37.6595)")
print("="*60)
try:
    from sqlalchemy import create_engine, and_, func as sqlfunc
    from sqlalchemy.orm import sessionmaker

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{WARN} DATABASE_URL not set -- skipping DB check")
    else:
        from app.models.climate_data import ClimateData

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()

        MOROGORO_LAT = -6.8211
        MOROGORO_LON = 37.6595
        TOL = 0.01

        total = db.query(sqlfunc.count(ClimateData.id)).filter(
            and_(
                ClimateData.location_lat.between(MOROGORO_LAT - TOL, MOROGORO_LAT + TOL),
                ClimateData.location_lon.between(MOROGORO_LON - TOL, MOROGORO_LON + TOL),
            )
        ).scalar()

        rain_count = db.query(sqlfunc.count(ClimateData.id)).filter(
            and_(
                ClimateData.location_lat.between(MOROGORO_LAT - TOL, MOROGORO_LAT + TOL),
                ClimateData.location_lon.between(MOROGORO_LON - TOL, MOROGORO_LON + TOL),
                ClimateData.rainfall_mm.isnot(None),
            )
        ).scalar()

        ndvi_count = db.query(sqlfunc.count(ClimateData.id)).filter(
            and_(
                ClimateData.location_lat.between(MOROGORO_LAT - TOL, MOROGORO_LAT + TOL),
                ClimateData.location_lon.between(MOROGORO_LON - TOL, MOROGORO_LON + TOL),
                ClimateData.ndvi.isnot(None),
            )
        ).scalar()

        latest_rain_date = db.query(sqlfunc.max(ClimateData.date)).filter(
            and_(
                ClimateData.location_lat.between(MOROGORO_LAT - TOL, MOROGORO_LAT + TOL),
                ClimateData.location_lon.between(MOROGORO_LON - TOL, MOROGORO_LON + TOL),
                ClimateData.rainfall_mm.isnot(None),
            )
        ).scalar()

        latest_ndvi_date = db.query(sqlfunc.max(ClimateData.date)).filter(
            and_(
                ClimateData.location_lat.between(MOROGORO_LAT - TOL, MOROGORO_LAT + TOL),
                ClimateData.location_lon.between(MOROGORO_LON - TOL, MOROGORO_LON + TOL),
                ClimateData.ndvi.isnot(None),
            )
        ).scalar()

        old_count = db.query(sqlfunc.count(ClimateData.id)).filter(
            and_(
                ClimateData.location_lat.between(-6.38, -6.35),
                ClimateData.location_lon.between(34.87, 34.90),
            )
        ).scalar()

        print(f"   Total records at Morogoro (+-0.01 deg): {total}")
        print(f"   Records with rainfall_mm : {rain_count}  (latest: {latest_rain_date})")
        print(f"   Records with ndvi        : {ndvi_count}  (latest: {latest_ndvi_date})")

        if old_count > 0:
            print(f"{WARN} {old_count} records at OLD wrong coords ~(-6.369, 34.888) !")
        else:
            print(f"{OK} No records at old wrong coords (-6.369, 34.888) -- clean")

        db.close()

except Exception as e:
    print(f"{WARN} DB check skipped or failed: {e}")

# ── 5. Forecast feature prep ──────────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 5: Forecast feature prep (can forecast service find data?)")
print("="*60)
try:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{WARN} DATABASE_URL not set -- skipping forecast feature prep check")
    else:
        from datetime import date
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.location import Location
        from app.services.forecast_service import ForecastGenerator

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()

        location = db.query(Location).filter(Location.id == 1).first()
        if not location:
            print(f"{WARN} Location id=1 not found in DB")
        else:
            print(f"   Location: {location.name} ({float(location.latitude):.4f}, "
                  f"{float(location.longitude):.4f})")
            gen = ForecastGenerator()
            features_df = gen.prepare_features(db, date.today(), horizon_months=3, location=location)
            if features_df is not None:
                print(f"{OK} Feature prep: {features_df.shape[1]} features, "
                      f"{features_df.shape[0]} rows")
            else:
                print(f"{ERR} Feature prep returned None -- "
                      f"not enough data for forecast generation")
        db.close()

except Exception as e:
    print(f"{WARN} Forecast feature prep skipped or failed: {e}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"  GEE auth : {OK if gee_ok else ERR + ' FAILED'}")
print(f"  CHIRPS   : {OK if chirps_ok else ERR + ' FAILED / empty'}")
print(f"  NDVI     : {OK if ndvi_ok else ERR + ' FAILED / empty'}")
print("="*60)

if not gee_ok:
    print("")
    print("ACTION NEEDED: GEE auth is broken.")
    print("  Check: GEE_SERVICE_ACCOUNT and GEE_PRIVATE_KEY_FILE env vars in .env")
    print("  Check: /app/secrets/gee-service-account.json exists and is valid")
    print("  OR:    run 'earthengine authenticate' inside the container")

all_ok = gee_ok and chirps_ok and ndvi_ok
sys.exit(0 if all_ok else 1)
