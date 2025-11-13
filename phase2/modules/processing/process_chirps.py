"""
CHIRPS Rainfall Data Processing - Phase 2
"""

import pandas as pd
from utils.validator import validate_dataframe
from utils.config import get_output_path

def process(data):
    """
    Process CHIRPS rainfall dataset (dry run version).
    """
    print("[PROCESS] Running CHIRPS rainfall data transformation (dry run)...")

    df = pd.DataFrame({
        "latitude": [0.0],
        "longitude": [0.0],
        "rainfall_mm": [12.5]
    })

    validate_dataframe(df, expected_columns=["latitude", "longitude", "rainfall_mm"])

    output_path = get_output_path("processed", "chirps_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"[SAVE] Processed output saved to {output_path}")
    print("[PROCESS] CHIRPS data processed successfully (dry run).")
    return df
