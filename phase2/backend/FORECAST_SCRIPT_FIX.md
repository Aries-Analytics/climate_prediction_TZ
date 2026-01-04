# Forecast Generation Script - Fix Guide

## Issues Identified

1. **Database doesn't exist**: PostgreSQL is running but the `climate_dev` database hasn't been created
2. **Deprecated pandas method**: Fixed `fillna(method='ffill')` → `ffill()`

## Quick Fix Steps

### Step 1: Create the Database

You need to create the PostgreSQL database. Choose one of these methods:

#### Option A: Using psql command line
```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE climate_dev;

# Grant permissions (if needed)
GRANT ALL PRIVILEGES ON DATABASE climate_dev TO user;

# Exit
\q
```

#### Option B: Using Python script
Create and run this script:

```python
# backend/create_database.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server (not to a specific database)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",  # Use your PostgreSQL admin user
    password="your_password"  # Use your PostgreSQL password
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create database
cursor = conn.cursor()
cursor.execute("CREATE DATABASE climate_dev")
cursor.close()
conn.close()

print("✓ Database 'climate_dev' created successfully!")
```

Run it:
```bash
cd backend
python create_database.py
```

### Step 2: Run Database Migrations

After creating the database, initialize the schema:

```bash
cd backend

# Run Alembic migrations to create tables
alembic upgrade head
```

### Step 3: Verify Database Setup

```bash
# Check if database exists
psql -U postgres -l | grep climate_dev

# Check if tables were created
psql -U postgres -d climate_dev -c "\dt"
```

You should see tables like:
- climate_data
- forecasts
- forecast_recommendations
- trigger_events
- users
- etc.

### Step 4: Run the Forecast Script

Now you can run the forecast generation script:

```bash
cd backend
python scripts/generate_real_forecasts.py
```

## Alternative: Use Docker

If you're having trouble with local PostgreSQL, use Docker:

```bash
# Start PostgreSQL with Docker
docker run --name climate-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=climate_dev \
  -p 5432:5432 \
  -d postgres:15

# Wait a few seconds for it to start
sleep 5

# Run migrations
cd backend
alembic upgrade head

# Run forecast script
python scripts/generate_real_forecasts.py
```

## Troubleshooting

### Error: "role 'user' does not exist"

Your PostgreSQL doesn't have the user specified in DATABASE_URL. Either:

1. Create the user:
```sql
CREATE USER "user" WITH PASSWORD 'pass';
GRANT ALL PRIVILEGES ON DATABASE climate_dev TO "user";
```

2. Or update `.env` to use your existing PostgreSQL user:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/climate_dev
```

### Error: "peer authentication failed"

Edit PostgreSQL's `pg_hba.conf` to allow password authentication:

```
# Change this line:
local   all             all                                     peer

# To this:
local   all             all                                     md5
```

Then restart PostgreSQL:
```bash
# Windows
net stop postgresql-x64-15
net start postgresql-x64-15

# Linux/Mac
sudo systemctl restart postgresql
```

### Error: "could not connect to server"

PostgreSQL isn't running. Start it:

```bash
# Windows
net start postgresql-x64-15

# Linux
sudo systemctl start postgresql

# Mac
brew services start postgresql
```

## What the Script Does

Once working, the script will:

1. ✓ Fetch last 180 days of climate data from 5 sources:
   - CHIRPS (rainfall)
   - NASA POWER (temperature)
   - ERA5 (atmospheric data)
   - NDVI (vegetation)
   - Ocean Indices (ENSO, IOD)

2. ✓ Merge and store data in database

3. ✓ Generate forecasts for 3-6 months ahead

4. ✓ Create recommendations for high-risk events

5. ✓ Display results and save to database

## Expected Output

```
============================================================
REAL-TIME FORECAST GENERATION
============================================================

[1/5] Fetching CHIRPS rainfall data...
✓ Fetched 6 CHIRPS records

[2/5] Fetching NASA POWER data...
✓ Fetched 6 NASA POWER records

...

✓ Stored 93 climate data records in database

============================================================
GENERATING FORECAST TIMELINE
============================================================

✓ Generated 108 forecasts

============================================================
✓ FORECAST GENERATION COMPLETE!
============================================================
```

## Need Help?

If you're still having issues:

1. Check PostgreSQL is installed: `psql --version`
2. Check PostgreSQL is running: `pg_isready`
3. Verify your credentials in `backend/.env`
4. Check the logs: `backend/logs/pipeline.log`
