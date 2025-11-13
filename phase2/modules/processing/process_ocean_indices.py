"""
Ocean Indices Data Processing - Phase 2
"""

import pandas as pd

from utils.config import get_output_path
from utils.validator import validate_dataframe


def process(data):
    """
    Process Ocean Indices dataset (dry run version).
    """
    print("[PROCESS] Running Ocean Indices data transformation (dry run)...")

    df = pd.DataFrame({"year": [2024], "month": ["Nov"], "enso_index": [0.34], "iod_index": [0.12]})

    validate_dataframe(df, expected_columns=["year", "month", "enso_index", "iod_index"])

    output_path = get_output_path("processed", "ocean_indices_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"[SAVE] Processed output saved to {output_path}")
    print("[PROCESS] Ocean Indices data processed successfully (dry run).")
    return df
