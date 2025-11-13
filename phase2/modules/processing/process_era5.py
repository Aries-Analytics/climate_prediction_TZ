"""
ERA5 Data Processing - Phase 2
"""

import pandas as pd
from utils.validator import validate_dataframe
from utils.config import get_output_path

def process(data):
    """
    Process ERA5 dataset (dry run version).
    """
    print("[PROCESS] Running ERA5 data transformation (dry run)...")

    df = pd.DataFrame({
        "latitude": [0.0],
        "longitude": [0.0],
        "temperature_c": [26.3],
        "humidity_percent": [74.0]
    })

    validate_dataframe(df, expected_columns=["latitude", "longitude", "temperature_c", "humidity_percent"])

    output_path = get_output_path("processed", "era5_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"[SAVE] Processed output saved to {output_path}")
    print("[PROCESS] ERA5 data processed successfully (dry run).")
    return df



    
