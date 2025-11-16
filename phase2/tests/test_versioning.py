"""
Tests for data versioning system
"""

import tempfile
from pathlib import Path

import pandas as pd
from utils.versioning import DataVersionControl


def test_create_version():
    """Test creating a new version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        # Create test data file
        df = pd.DataFrame({"year": [2020, 2021], "value": [100, 200]})
        data_path = Path(tmpdir) / "test_data.csv"
        df.to_csv(data_path, index=False)

        # Create version
        version = vc.create_version("test_dataset", data_path, description="Initial version")

        assert version == 1
        assert "test_dataset" in vc.metadata


def test_list_versions():
    """Test listing versions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        df = pd.DataFrame({"year": [2020], "value": [100]})
        data_path = Path(tmpdir) / "test_data.csv"
        df.to_csv(data_path, index=False)

        # Create multiple versions
        vc.create_version("test_dataset", data_path, description="Version 1")
        vc.create_version("test_dataset", data_path, description="Version 2")

        versions = vc.list_versions("test_dataset")
        assert len(versions) == 2


def test_get_version():
    """Test retrieving a specific version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        df = pd.DataFrame({"year": [2020], "value": [100]})
        data_path = Path(tmpdir) / "test_data.csv"
        df.to_csv(data_path, index=False)

        vc.create_version("test_dataset", data_path)

        version_path = vc.get_version("test_dataset", version=1)
        assert version_path is not None
        assert version_path.exists()


def test_rollback():
    """Test rolling back to a previous version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        # Create version 1
        df1 = pd.DataFrame({"year": [2020], "value": [100]})
        data_path = Path(tmpdir) / "test_data.csv"
        df1.to_csv(data_path, index=False)
        vc.create_version("test_dataset", data_path, description="Version 1")

        # Create version 2
        df2 = pd.DataFrame({"year": [2020, 2021], "value": [100, 200]})
        df2.to_csv(data_path, index=False)
        vc.create_version("test_dataset", data_path, description="Version 2")

        # Rollback to version 1
        target_path = Path(tmpdir) / "restored.csv"
        success = vc.rollback("test_dataset", 1, target_path)

        assert success is True
        assert target_path.exists()

        # Verify rolled back data
        restored_df = pd.read_csv(target_path)
        assert len(restored_df) == 1


def test_compare_versions():
    """Test comparing two versions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        # Create version 1
        df1 = pd.DataFrame({"year": [2020], "value": [100]})
        data_path = Path(tmpdir) / "test_data.csv"
        df1.to_csv(data_path, index=False)
        vc.create_version("test_dataset", data_path)

        # Create version 2
        df2 = pd.DataFrame({"year": [2020, 2021], "value": [100, 200]})
        df2.to_csv(data_path, index=False)
        vc.create_version("test_dataset", data_path)

        # Compare versions
        comparison = vc.compare_versions("test_dataset", 1, 2)

        assert comparison is not None
        assert "row_diff" in comparison
        assert comparison["row_diff"] == 1


def test_get_current_version():
    """Test getting current version number."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = DataVersionControl(versions_dir=tmpdir)

        df = pd.DataFrame({"year": [2020], "value": [100]})
        data_path = Path(tmpdir) / "test_data.csv"
        df.to_csv(data_path, index=False)

        vc.create_version("test_dataset", data_path)
        vc.create_version("test_dataset", data_path)

        current = vc.get_current_version("test_dataset")
        assert current == 2
