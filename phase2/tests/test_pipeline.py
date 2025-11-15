import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest  # noqa: E402

run_pipeline = pytest.importorskip("run_pipeline", reason="run_pipeline module not available")  # noqa: E402


@pytest.mark.pipeline
def test_pipeline_dry_run():
    """Dry-run test: executes the full Phase 2 pipeline"""
    run_pipeline.run_pipeline(debug=True)
    assert True
