import pandas as pd

df = pd.read_csv('outputs/processed/master_dataset.csv')

print("=== TRIGGER COLUMN INVESTIGATION ===\n")

trigger_cols = ['drought_trigger', 'flood_trigger', 'crop_failure_trigger']

for col in trigger_cols:
    if col in df.columns:
        print(f"\n{col}:")
        print(f"  Data type: {df[col].dtype}")
        print(f"  Unique values: {sorted(df[col].unique())}")
        print(f"  Value counts:")
        for val, count in df[col].value_counts().items():
            print(f"    {val}: {count}")
    else:
        print(f"\n{col}: NOT FOUND")

print("\n=== SAMPLE ROWS WITH TRIGGERS ===")
for col in trigger_cols:
    if col in df.columns:
        # Try different trigger conditions
        triggered_1 = df[df[col] == 1]
        triggered_true = df[df[col] == True]
        triggered_nonzero = df[df[col] > 0]
        
        print(f"\n{col}:")
        print(f"  Rows where {col} == 1: {len(triggered_1)}")
        print(f"  Rows where {col} == True: {len(triggered_true)}")
        print(f"  Rows where {col} > 0: {len(triggered_nonzero)}")
        
        if len(triggered_nonzero) > 0:
            print(f"\n  Sample triggered row:")
            sample = triggered_nonzero.iloc[0]
            print(f"    Location: {sample.get('location', 'N/A')}")
            print(f"    Year: {sample.get('year', 'N/A')}, Month: {sample.get('month', 'N/A')}")
            print(f"    Trigger value: {sample[col]}")
