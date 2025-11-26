import sys
sys.path.append('.')

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
import pandas as pd

db = SessionLocal()

# Tanzania coordinates
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822

# Query climate data
climate = db.query(ClimateData).filter(
    ClimateData.location_lat == TANZANIA_LAT,
    ClimateData.location_lon == TANZANIA_LON
).order_by(ClimateData.date).all()

print(f"\n=== CLIMATE DATA ANALYSIS ===")
print(f"Total climate records: {len(climate)}")

# Convert to DataFrame
data = []
for c in climate:
    data.append({
        'date': c.date,
        'year': c.date.year,
        'month': c.date.month,
        'rainfall': float(c.rainfall_mm) if c.rainfall_mm else 0,
        'temperature': float(c.temperature_avg) if c.temperature_avg else 0,
        'ndvi': float(c.ndvi) if c.ndvi else 0
    })

df = pd.DataFrame(data)

print(f"\n=== RAINFALL ANALYSIS BY YEAR ===")
yearly_rain = df.groupby('year')['rainfall'].agg(['mean', 'sum', 'count'])
print(yearly_rain)

print(f"\n=== 2018 DROUGHT ANALYSIS ===")
df_2018 = df[df['year'] == 2018]
print(f"2018 Average rainfall: {df_2018['rainfall'].mean():.2f} mm")
print(f"2018 Monthly rainfall:")
print(df_2018[['date', 'rainfall']].to_string(index=False))

print(f"\n=== 2020-2022 RAINFALL ANALYSIS ===")
df_2020_2022 = df[(df['year'] >= 2020) & (df['year'] <= 2022)]
print(f"2020-2022 Average rainfall: {df_2020_2022['rainfall'].mean():.2f} mm")
print(f"\nMonthly rainfall 2020-2022:")
print(df_2020_2022.groupby('year')['rainfall'].agg(['mean', 'min', 'max']))

print(f"\n=== COMPARISON: 2018 vs 2020-2022 ===")
rain_2018 = df_2018['rainfall'].mean()
rain_2020_2022 = df_2020_2022['rainfall'].mean()
print(f"2018 avg rainfall: {rain_2018:.2f} mm")
print(f"2020-2022 avg rainfall: {rain_2020_2022:.2f} mm")
print(f"Difference: {rain_2020_2022 - rain_2018:.2f} mm ({((rain_2020_2022/rain_2018 - 1) * 100):.1f}% change)")

print(f"\n=== NDVI ANALYSIS (Vegetation Health) ===")
print(f"2018 avg NDVI: {df_2018['ndvi'].mean():.3f}")
print(f"2020-2022 avg NDVI: {df_2020_2022['ndvi'].mean():.3f}")

db.close()
