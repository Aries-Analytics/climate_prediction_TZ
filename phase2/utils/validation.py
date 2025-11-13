"""
Validation and summary utilities for Phase 2 pipeline.
"""

import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_dataframe(df, name: str) -> bool:
    """Validate that the input is a non-empty pandas DataFrame."""
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"[{name}] Expected a pandas DataFrame, got {type(df)}")
        return False

    if df.empty:
        logger.warning(f"[{name}] DataFrame is empty!")
        return False

    logger.info(f"[{name}] DataFrame validation passed.")
    return True


def log_dataframe_summary(df: pd.DataFrame, name: str, sample_rows: int = 3):
    """Log a concise summary of a DataFrame."""
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"[{name}] Cannot summarize non-DataFrame object.")
        return

    logger.info(f"[{name}] Shape: {df.shape}")
    logger.info(f"[{name}] Columns: {list(df.columns)}")
    logger.debug(f"[{name}] Sample:\n{df.head(sample_rows).to_string(index=False)}")
