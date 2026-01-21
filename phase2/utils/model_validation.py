"""
Automated Model Validation Pipeline

This module provides automated checks for model quality, identifying potential
issues like overfitting, insufficient data, and poor baseline comparisons.

Key features:
- Feature-to-sample ratio validation
- Train-validation gap detection
- Test set size validation
- Baseline comparison checks
- Comprehensive pass/fail reporting

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Severity levels for validation issues."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ValidationCheck:
    """Container for a single validation check result."""

    name: str
    passed: bool
    severity: Severity
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: Optional[str] = None


@dataclass
class ValidationReport:
    """Container for complete validation report."""

    timestamp: datetime
    model_name: str
    feature_to_sample_ratio: float
    train_val_gap: float
    test_set_size: int
    overfitting_severity: str
    baseline_comparison: Dict[str, float]
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    checks_warning: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    overall_status: Severity = Severity.PASS
    all_checks: List[ValidationCheck] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model_name": self.model_name,
            "feature_to_sample_ratio": self.feature_to_sample_ratio,
            "train_val_gap": self.train_val_gap,
            "test_set_size": self.test_set_size,
            "overfitting_severity": self.overfitting_severity,
            "baseline_comparison": self.baseline_comparison,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks_warning": self.checks_warning,
            "recommendations": self.recommendations,
            "overall_status": self.overall_status.value,
            "all_checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "severity": check.severity.value,
                    "message": check.message,
                    "value": check.value,
                    "threshold": check.threshold,
                    "recommendation": check.recommendation,
                }
                for check in self.all_checks
            ],
        }

    def summary(self) -> str:
        """Generate a summary string of the validation report."""
        summary = f"\n{'='*70}\n"
        summary += f"MODEL VALIDATION REPORT: {self.model_name}\n"
        summary += f"{'='*70}\n"
        summary += f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"Overall Status: {self.overall_status.value.upper()}\n"
        summary += f"\n{'='*70}\n"
        summary += f"KEY METRICS\n"
        summary += f"{'='*70}\n"
        summary += f"Feature-to-Sample Ratio: {self.feature_to_sample_ratio:.2f}:1\n"
        summary += f"Train-Validation Gap: {self.train_val_gap:.2%}\n"
        summary += f"Test Set Size: {self.test_set_size} samples\n"
        summary += f"Overfitting Severity: {self.overfitting_severity}\n"

        summary += f"\n{'='*70}\n"
        summary += f"VALIDATION CHECKS\n"
        summary += f"{'='*70}\n"
        summary += f"✓ Passed: {len(self.checks_passed)}\n"
        summary += f"⚠ Warnings: {len(self.checks_warning)}\n"
        summary += f"✗ Failed: {len(self.checks_failed)}\n"

        if self.checks_failed:
            summary += f"\nFailed Checks:\n"
            for check in self.checks_failed:
                summary += f"  ✗ {check}\n"

        if self.checks_warning:
            summary += f"\nWarnings:\n"
            for check in self.checks_warning:
                summary += f"  ⚠ {check}\n"

        if self.recommendations:
            summary += f"\n{'='*70}\n"
            summary += f"RECOMMENDATIONS\n"
            summary += f"{'='*70}\n"
            for i, rec in enumerate(self.recommendations, 1):
                summary += f"{i}. {rec}\n"

        summary += f"{'='*70}\n"
        return summary


def check_feature_to_sample_ratio(n_features: int, n_samples: int, min_ratio: float = 5.0) -> ValidationCheck:
    """
    Check if feature-to-sample ratio is healthy.

    Standard ML practice: aim for at least 5-10 samples per feature.

    Args:
        n_features: Number of features
        n_samples: Number of training samples
        min_ratio: Minimum acceptable samples per feature (default 5.0)

    Returns:
        ValidationCheck object

    Requirements: 10.1
    """
    ratio = n_samples / n_features if n_features > 0 else 0
    passed = ratio >= min_ratio

    if ratio >= 10:
        severity = Severity.PASS
        message = f"Excellent feature-to-sample ratio: {ratio:.2f}:1 (>= 10:1 is ideal)"
        recommendation = None
    elif ratio >= min_ratio:
        severity = Severity.PASS
        message = f"Acceptable feature-to-sample ratio: {ratio:.2f}:1 (>= {min_ratio}:1)"
        recommendation = "Consider feature selection to improve ratio further"
    elif ratio >= 2:
        severity = Severity.WARNING
        message = f"Low feature-to-sample ratio: {ratio:.2f}:1 (< {min_ratio}:1)"
        recommendation = "Apply feature selection to reduce dimensionality. Target: 50-100 features"
    else:
        severity = Severity.FAIL
        message = f"Critical feature-to-sample ratio: {ratio:.2f}:1 (< 2:1)"
        recommendation = "URGENT: Reduce features dramatically or collect more data. High overfitting risk!"

    return ValidationCheck(
        name="Feature-to-Sample Ratio",
        passed=passed,
        severity=severity,
        message=message,
        value=ratio,
        threshold=min_ratio,
        recommendation=recommendation,
    )


def check_train_val_gap(train_r2: float, val_r2: float, max_gap: float = 0.05) -> ValidationCheck:
    """
    Check if train-validation performance gap indicates overfitting.

    Args:
        train_r2: R² score on training set
        val_r2: R² score on validation set
        max_gap: Maximum acceptable gap (default 0.05 = 5%)

    Returns:
        ValidationCheck object

    Requirements: 10.2
    """
    gap = abs(train_r2 - val_r2)
    passed = gap <= max_gap

    if gap <= 0.02:
        severity = Severity.PASS
        message = f"Excellent train-val gap: {gap:.2%} (<= 2%)"
        recommendation = None
    elif gap <= max_gap:
        severity = Severity.PASS
        message = f"Acceptable train-val gap: {gap:.2%} (<= {max_gap:.0%})"
        recommendation = None
    elif gap <= 0.10:
        severity = Severity.WARNING
        message = f"Moderate overfitting detected: {gap:.2%} gap"
        recommendation = "Apply stronger regularization or reduce model complexity"
    else:
        severity = Severity.FAIL
        message = f"Severe overfitting detected: {gap:.2%} gap (> 10%)"
        recommendation = "URGENT: Apply strong regularization, reduce features, or simplify model"

    return ValidationCheck(
        name="Train-Validation Gap",
        passed=passed,
        severity=severity,
        message=message,
        value=gap,
        threshold=max_gap,
        recommendation=recommendation,
    )


def check_test_set_size(test_size: int, min_size: int = 50) -> ValidationCheck:
    """
    Check if test set is large enough for reliable evaluation.

    Args:
        test_size: Number of test samples
        min_size: Minimum acceptable test size (default 50)

    Returns:
        ValidationCheck object

    Requirements: 10.3
    """
    passed = test_size >= min_size

    if test_size >= 100:
        severity = Severity.PASS
        message = f"Good test set size: {test_size} samples (>= 100)"
        recommendation = None
    elif test_size >= min_size:
        severity = Severity.PASS
        message = f"Acceptable test set size: {test_size} samples (>= {min_size})"
        recommendation = "Consider collecting more data for more robust evaluation"
    elif test_size >= 30:
        severity = Severity.WARNING
        message = f"Small test set: {test_size} samples (< {min_size})"
        recommendation = "Metrics may have high variance. Use cross-validation for robust estimates"
    else:
        severity = Severity.FAIL
        message = f"Very small test set: {test_size} samples (< 30)"
        recommendation = "URGENT: Test set too small for reliable evaluation. Use cross-validation"

    return ValidationCheck(
        name="Test Set Size",
        passed=passed,
        severity=severity,
        message=message,
        value=float(test_size),
        threshold=float(min_size),
        recommendation=recommendation,
    )


def check_baseline_improvement(model_r2: float, baseline_r2: float, min_improvement: float = 0.10) -> ValidationCheck:
    """
    Check if model improves significantly over baseline.

    Args:
        model_r2: Model R² score
        baseline_r2: Baseline R² score
        min_improvement: Minimum improvement required (default 0.10 = 10%)

    Returns:
        ValidationCheck object

    Requirements: 10.4
    """
    improvement = model_r2 - baseline_r2
    passed = improvement >= min_improvement

    if improvement >= 0.20:
        severity = Severity.PASS
        message = f"Excellent improvement over baseline: +{improvement:.2%} (>= 20%)"
        recommendation = None
    elif improvement >= min_improvement:
        severity = Severity.PASS
        message = f"Good improvement over baseline: +{improvement:.2%} (>= {min_improvement:.0%})"
        recommendation = None
    elif improvement >= 0.05:
        severity = Severity.WARNING
        message = f"Modest improvement over baseline: +{improvement:.2%} (< {min_improvement:.0%})"
        recommendation = "Model may be too complex for marginal gains. Consider simpler approaches"
    else:
        severity = Severity.FAIL
        message = f"Insufficient improvement over baseline: +{improvement:.2%} (< 5%)"
        recommendation = "URGENT: Model doesn't justify complexity. Use simpler baseline or collect more data"

    return ValidationCheck(
        name="Baseline Improvement",
        passed=passed,
        severity=severity,
        message=message,
        value=improvement,
        threshold=min_improvement,
        recommendation=recommendation,
    )


def determine_overfitting_severity(train_r2: float, val_r2: float) -> str:
    """
    Determine overfitting severity based on train-val gap.

    Args:
        train_r2: Training R² score
        val_r2: Validation R² score

    Returns:
        Severity level: 'low', 'medium', or 'high'
    """
    gap = abs(train_r2 - val_r2)

    if gap <= 0.02:
        return "low"
    elif gap <= 0.05:
        return "medium"
    else:
        return "high"


def validate_model(
    model_name: str,
    n_features: int,
    n_train_samples: int,
    n_test_samples: int,
    train_r2: float,
    val_r2: float,
    test_r2: float,
    baseline_r2: Optional[float] = None,
) -> ValidationReport:
    """
    Run complete validation pipeline on a trained model.

    Args:
        model_name: Name of the model
        n_features: Number of features used
        n_train_samples: Number of training samples
        n_test_samples: Number of test samples
        train_r2: Training R² score
        val_r2: Validation R² score
        test_r2: Test R² score
        baseline_r2: Baseline model R² score (optional)

    Returns:
        ValidationReport with all checks and recommendations

    Requirements: 10.5
    """
    logger.info(f"Running validation pipeline for {model_name}")

    checks = []

    # Check 1: Feature-to-sample ratio
    check1 = check_feature_to_sample_ratio(n_features, n_train_samples)
    checks.append(check1)

    # Check 2: Train-validation gap
    check2 = check_train_val_gap(train_r2, val_r2)
    checks.append(check2)

    # Check 3: Test set size
    check3 = check_test_set_size(n_test_samples)
    checks.append(check3)

    # Check 4: Baseline improvement (if baseline provided)
    if baseline_r2 is not None:
        check4 = check_baseline_improvement(test_r2, baseline_r2)
        checks.append(check4)

    # Categorize checks
    checks_passed = []
    checks_failed = []
    checks_warning = []
    recommendations = []

    for check in checks:
        if check.severity == Severity.PASS:
            checks_passed.append(check.message)
        elif check.severity == Severity.WARNING:
            checks_warning.append(check.message)
        else:  # FAIL
            checks_failed.append(check.message)

        if check.recommendation:
            recommendations.append(check.recommendation)

    # Determine overall status
    if checks_failed:
        overall_status = Severity.FAIL
    elif checks_warning:
        overall_status = Severity.WARNING
    else:
        overall_status = Severity.PASS

    # Calculate metrics
    feature_to_sample_ratio = n_train_samples / n_features if n_features > 0 else 0
    train_val_gap = abs(train_r2 - val_r2)
    overfitting_severity = determine_overfitting_severity(train_r2, val_r2)

    baseline_comparison = {
        "model_r2": test_r2,
        "baseline_r2": baseline_r2 if baseline_r2 is not None else None,
        "improvement": test_r2 - baseline_r2 if baseline_r2 is not None else None,
    }

    # Create report
    report = ValidationReport(
        timestamp=datetime.now(),
        model_name=model_name,
        feature_to_sample_ratio=feature_to_sample_ratio,
        train_val_gap=train_val_gap,
        test_set_size=n_test_samples,
        overfitting_severity=overfitting_severity,
        baseline_comparison=baseline_comparison,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        checks_warning=checks_warning,
        recommendations=list(set(recommendations)),  # Remove duplicates
        overall_status=overall_status,
        all_checks=checks,
    )

    logger.info(f"Validation complete: {overall_status.value.upper()}")
    logger.info(f"  Passed: {len(checks_passed)}, Warnings: {len(checks_warning)}, Failed: {len(checks_failed)}")

    return report


def save_validation_report(report: ValidationReport, filepath: str):
    """
    Save validation report to JSON file.

    Args:
        report: ValidationReport object
        filepath: Path to save JSON file
    """
    import json
    from pathlib import Path

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    logger.info(f"Validation report saved to {filepath}")
