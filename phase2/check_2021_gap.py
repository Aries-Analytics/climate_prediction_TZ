"""Quick script to check trigger gaps in 2021"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/climate_insurance"
engine = create_engine(DATABASE_URL)

# Query triggers in 2021
query = """
SELECT 
    date,
    trigger_type,
    severity,
    confidence,
    payout_amount
FROM trigger_events
WHERE EXTRACT(YEAR FROM date) = 2021
ORDER BY date;
"""

with engine.connect() as conn:
    df = pd.read_sql(query, conn)
    
print(f"\n=== TRIGGERS IN 2021 ===")
print(f"Total triggers: {len(df)}")
print(f"\nTriggers by month:")
if len(df) > 0:
    df['month'] = pd.to_datetime(df['date']).dt.month
    print(df.groupby('month').size())
    print(f"\nAll 2021 triggers:")
    print(df[['date', 'trigger_type', 'severity', 'confidence']])
else:
    print("No triggers found in 2021")

# Query climate data for June-Sept 2021
climate_query = """
SELECT 
    date,
    rainfall_mm,
    temperature_c,
    spi_30day,
    consecutive_dry_days
FROM climate_data
WHERE date >= '2021-06-01' AND date <= '2021-09-30'
ORDER BY date;
"""

print(f"\n=== CLIMATE DATA: JUNE-SEPT 2021 ===")
with engine.connect() as conn:
    climate_df = pd.read_sql(climate_query, conn)
    
if len(climate_df) > 0:
    print(f"Records: {len(climate_df)}")
    print(f"\nRainfall statistics:")
    print(climate_df['rainfall_mm'].describe())
    print(f"\nSPI-30 statistics:")
    print(climate_df['spi_30day'].describe())
    print(f"\nConsecutive dry days statistics:")
    print(climate_df['consecutive_dry_days'].describe())
    print(f"\nDays with rainfall < 1mm: {(climate_df['rainfall_mm'] < 1).sum()}")
    print(f"\nSample data:")
    print(climate_df.head(10))
else:
    print("No climate data found for June-Sept 2021")
