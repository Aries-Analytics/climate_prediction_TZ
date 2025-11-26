import sys
sys.path.append('.')

from app.core.database import SessionLocal
from app.models.trigger_event import TriggerEvent
from sqlalchemy import func, extract
import pandas as pd

db = SessionLocal()

# Query all triggers
triggers = db.query(TriggerEvent).order_by(TriggerEvent.date).all()

print(f"\n=== TRIGGER EVENT ANALYSIS ===")
print(f"Total triggers in database: {len(triggers)}")

# Convert to DataFrame for analysis
data = []
for t in triggers:
    data.append({
        'date': t.date,
        'year': t.date.year,
        'trigger_type': t.trigger_type,
        'severity': float(t.severity) if t.severity else 0,
        'confidence': float(t.confidence) if t.confidence else 0,
        'payout': float(t.payout_amount) if t.payout_amount else 0
    })

df = pd.DataFrame(data)

print(f"\n=== TRIGGERS BY YEAR ===")
print(df.groupby('year').size())

print(f"\n=== TRIGGERS BY YEAR AND TYPE ===")
print(df.groupby(['year', 'trigger_type']).size())

print(f"\n=== GAP ANALYSIS: 2020-2022 ===")
gap_period = df[(df['year'] >= 2020) & (df['year'] <= 2022)]
print(f"Triggers in 2020-2022: {len(gap_period)}")
print(gap_period.groupby(['year', 'trigger_type']).size())

print(f"\n=== HIGH SEVERITY EVENTS IN 2018 ===")
early_2018 = df[(df['year'] == 2018) & (df['severity'] >= 0.5)]
print(f"Events with severity >= 50% in 2018: {len(early_2018)}")
print(early_2018[['date', 'trigger_type', 'severity', 'confidence']])

print(f"\n=== SEVERITY DISTRIBUTION ===")
print(df['severity'].describe())

print(f"\n=== DATE RANGE ===")
print(f"First trigger: {df['date'].min()}")
print(f"Last trigger: {df['date'].max()}")

db.close()
