"""
Data Versioning System - Phase 2
Provides version control for climate datasets with metadata tracking and rollback capabilities.
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.config import get_data_path
from utils.logger import log_error, log_info


class DataVersionControl:
    """
    Manages versioning for climate datasets.
    Tracks changes, maintains version history, and enables rollback.
    """

    def __init__(self, versions_dir=None):
        """
        Initialize the version control system.

        Args:
            versions_dir: Directory to store versions (default: data/versions)
        """
        if versions_dir is None:
            versions_dir = get_data_path("versions")
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.versions_dir / "version_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        """Load version metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                log_error(f"Failed to load version metadata: {e}")
        return {}

    def _save_metadata(self):
        """Save version metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            log_error(f"Failed to save version metadata: {e}")

    def _calculate_checksum(self, filepath):
        """Calculate MD5 checksum of a file."""
        md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _get_version_path(self, dataset_name, version):
        """Get the file path for a specific version."""
        return self.versions_dir / dataset_name / f"v{version}.csv"

    def create_version(self, dataset_name, data_path, description="", tags=None):
        """
        Create a new version of a dataset.

        Args:
            dataset_name: Name of the dataset
            data_path: Path to the current data file
            description: Description of changes in this version
            tags: List of tags for this version

        Returns:
            Version number created
        """
        try:
            data_path = Path(data_path)
            if not data_path.exists():
                log_error(f"Data file not found: {data_path}")
                return None

            # Initialize dataset metadata if not exists
            if dataset_name not in self.metadata:
                self.metadata[dataset_name] = {"versions": [], "current_version": 0}

            # Determine next version number
            version_num = len(self.metadata[dataset_name]["versions"]) + 1

            # Create version directory
            version_path = self._get_version_path(dataset_name, version_num)
            version_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy data file to version storage
            shutil.copy2(data_path, version_path)

            # Calculate checksum
            checksum = self._calculate_checksum(version_path)

            # Get file size
            file_size = version_path.stat().st_size

            # Create version metadata
            version_info = {
                "version": version_num,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "tags": tags or [],
                "checksum": checksum,
                "file_size": file_size,
                "file_path": str(version_path),
            }

            # Add row count if it's a CSV
            try:
                df = pd.read_csv(version_path)
                version_info["row_count"] = len(df)
                version_info["column_count"] = len(df.columns)
            except Exception:
                pass

            # Update metadata
            self.metadata[dataset_name]["versions"].append(version_info)
            self.metadata[dataset_name]["current_version"] = version_num
            self._save_metadata()

            log_info(f"Created version {version_num} for {dataset_name}")
            return version_num

        except Exception as e:
            log_error(f"Failed to create version: {e}")
            return None

    def get_version(self, dataset_name, version=None):
        """
        Get a specific version of a dataset.

        Args:
            dataset_name: Name of the dataset
            version: Version number (None for current version)

        Returns:
            Path to the version file
        """
        if dataset_name not in self.metadata:
            log_error(f"Dataset not found: {dataset_name}")
            return None

        if version is None:
            version = self.metadata[dataset_name]["current_version"]

        version_path = self._get_version_path(dataset_name, version)
        if version_path.exists():
            return version_path
        else:
            log_error(f"Version {version} not found for {dataset_name}")
            return None

    def list_versions(self, dataset_name):
        """
        List all versions of a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List of version metadata
        """
        if dataset_name not in self.metadata:
            return []
        return self.metadata[dataset_name]["versions"]

    def get_version_info(self, dataset_name, version):
        """
        Get metadata for a specific version.

        Args:
            dataset_name: Name of the dataset
            version: Version number

        Returns:
            Version metadata dictionary
        """
        versions = self.list_versions(dataset_name)
        for v in versions:
            if v["version"] == version:
                return v
        return None

    def rollback(self, dataset_name, version, target_path):
        """
        Rollback to a previous version.

        Args:
            dataset_name: Name of the dataset
            version: Version number to rollback to
            target_path: Path where to restore the version

        Returns:
            True if successful, False otherwise
        """
        try:
            version_path = self.get_version(dataset_name, version)
            if version_path is None:
                return False

            # Copy version file to target path
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(version_path, target_path)

            log_info(f"Rolled back {dataset_name} to version {version}")
            return True

        except Exception as e:
            log_error(f"Failed to rollback: {e}")
            return False

    def compare_versions(self, dataset_name, version1, version2):
        """
        Compare two versions of a dataset.

        Args:
            dataset_name: Name of the dataset
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with comparison results
        """
        try:
            info1 = self.get_version_info(dataset_name, version1)
            info2 = self.get_version_info(dataset_name, version2)

            if info1 is None or info2 is None:
                return None

            comparison = {
                "version1": version1,
                "version2": version2,
                "checksum_match": info1["checksum"] == info2["checksum"],
                "size_diff": info2["file_size"] - info1["file_size"],
                "timestamp1": info1["timestamp"],
                "timestamp2": info2["timestamp"],
            }

            # Compare row counts if available
            if "row_count" in info1 and "row_count" in info2:
                comparison["row_diff"] = info2["row_count"] - info1["row_count"]

            return comparison

        except Exception as e:
            log_error(f"Failed to compare versions: {e}")
            return None

    def delete_version(self, dataset_name, version):
        """
        Delete a specific version.

        Args:
            dataset_name: Name of the dataset
            version: Version number to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if dataset_name not in self.metadata:
                return False

            # Don't allow deleting current version
            if version == self.metadata[dataset_name]["current_version"]:
                log_error("Cannot delete current version")
                return False

            # Remove version file
            version_path = self._get_version_path(dataset_name, version)
            if version_path.exists():
                version_path.unlink()

            # Remove from metadata
            versions = self.metadata[dataset_name]["versions"]
            self.metadata[dataset_name]["versions"] = [v for v in versions if v["version"] != version]
            self._save_metadata()

            log_info(f"Deleted version {version} of {dataset_name}")
            return True

        except Exception as e:
            log_error(f"Failed to delete version: {e}")
            return False

    def get_current_version(self, dataset_name):
        """
        Get the current version number for a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Current version number or None
        """
        if dataset_name in self.metadata:
            return self.metadata[dataset_name]["current_version"]
        return None


# Global version control instance
_version_control = None


def get_version_control(versions_dir=None):
    """
    Get or create the global version control instance.

    Args:
        versions_dir: Directory to store versions

    Returns:
        DataVersionControl instance
    """
    global _version_control
    if _version_control is None:
        _version_control = DataVersionControl(versions_dir=versions_dir)
    return _version_control
