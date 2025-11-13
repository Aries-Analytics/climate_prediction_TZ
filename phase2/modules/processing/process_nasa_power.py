"""
NASA POWER Data Processing - Phase 2
"""

import pandas as pd
from utils.validator import validate_dataframe
from utils.config import get_output_path

def process(data):
    """
    Process NASA POWER dataset (dry run version).

    Args:
        data: Input data placeholder

    Returns:
        pd.DataFrame: Processed dataset placeholder
    """
    print("[PROCESS] Running NASA POWER data transformation (dry run)...")

    df = pd.DataFrame({
        "latitude": [0.0],
        "longitude": [0.0],
        "temperature_c": [25.0],
        "solar_radiation_wm2": [210.5]
    })

    validate_dataframe(df, expected_columns=["latitude", "longitude", "temperature_c", "solar_radiation_wm2"])

    output_path = get_output_path("processed", "nasa_power_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"[SAVE] Processed output saved to {output_path}")
    print("[PROCESS] NASA POWER data processed successfully (dry run).")
    return df


