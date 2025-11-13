"""
NDVI Vegetation Index Data Processing - Phase 2
"""

import pandas as pd
from utils.validator import validate_dataframe
from utils.config import get_output_path

def process(data):
    """
    Process NDVI vegetation index dataset (dry run version).
    """
    print("[PROCESS] Running NDVI data transformation (dry run)...")

    df = pd.DataFrame({
        "latitude": [0.0],
        "longitude": [0.0],
        "ndvi": [0.68]
    })

    validate_dataframe(df, expected_columns=["latitude", "longitude", "ndvi"])

    output_path = get_output_path("processed", "ndvi_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"[SAVE] Processed output saved to {output_path}")
    print("[PROCESS] NDVI data processed successfully (dry run).")
    return df


