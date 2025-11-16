from pathlib import Path

import pytest

run_pipeline = pytest.importorskip("run_pipeline", reason="run_pipeline module not available")

from modules.processing import merge_processed  # noqa: E402
from utils.config import get_output_path  # noqa: E402


def test_merge_creates_master(tmp_path):
    """
    Run merge_all() and ensure master_dataset.csv/parquet exist and DataFrame returned is non-empty.
    First runs the pipeline to create processed CSVs.
    """
    # run pipeline first to create processed files
    run_pipeline.run_pipeline(debug=True)

    # run merge
    merged = merge_processed.merge_all()
    assert merged is not None
    assert hasattr(merged, "shape")
    assert merged.shape[0] > 0

    # check files created
    csv_p = get_output_path("processed", "master_dataset.csv")
    parquet_p = get_output_path("processed", "master_dataset.parquet")
    assert Path(csv_p).exists()
    assert Path(parquet_p).exists()
