import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest

import run_pipeline


@pytest.mark.pipeline
def test_pipeline_dry_run():
    """Dry-run test: executes the full Phase 2 pipeline"""
    run_pipeline.run_pipeline(debug=True)
    assert True
