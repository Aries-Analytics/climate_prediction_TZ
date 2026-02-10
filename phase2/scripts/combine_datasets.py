import pandas as pd

# Combine train/val/test as documented in 6_LOCATION_EXPANSION_SUMMARY.md
train = pd.read_csv('outputs/processed/features_train.csv')
val = pd.read_csv('outputs/processed/features_val.csv')
test = pd.read_csv('outputs/processed/features_test.csv')

print(f"Train: {train.shape}")
print(f"Val: {val.shape}")
print(f"Test: {test.shape}")

master = pd.concat([train, val, test], ignore_index=True)

print(f"\nCombined master dataset:")
print(f"  Records: {len(master)}")
print(f"  Locations: {master['location'].nunique() if 'location' in master.columns else 'N/A'}")
if 'location' in master.columns:
    print(f"  Location list: {sorted(master['location'].unique())}")
if 'year' in master.columns:
    print(f"  Years: {master['year'].min()} - {master['year'].max()}")

# Save
master.to_csv('data/processed/master_dataset_full.csv', index=False)
print(f"\n✓ Saved to data/processed/master_dataset_full.csv")
