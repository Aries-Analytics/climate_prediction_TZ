"""
Data Quality Validation Script

Validates data ranges, distributions, and consistency against expected baselines.

Usage:
    python scripts/validate_data_quality.py
    python scripts/validate_data_quality.py --source CHIRPS
    python scripts/validate_data_quality.py --send-alerts
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from utils.slack_notifier import send_data_quality_alert

# Load environment
load_dotenv()


# Expected data ranges for each source
EXPECTED_RANGES = {
    "CHIRPS": {
        "variable": "rainfall_mm",
        "min": 0,
        "max": 800,
        "typical_max": 500
    },
    "NASA_POWER": {
        "temperature": {"min": 10, "max": 45, "typical_max": 38},
        "humidity": {"min": 0, "max": 100, "typical_max": 100},
        "solar_radiation": {"min": 0, "max": 30, "typical_max": 25}
    },
    "NDVI": {
        "variable": "ndvi",
        "min": 0,
        "max": 1,
        "typical_max": 0.95
    },
    "OCEAN_INDICES": {
        "oni": {"min": -3, "max": 3, "typical_max": 2.5},
        "iod": {"min": -2, "max": 2, "typical_max": 1.5}
    }
}


class DataQualityValidator:
    """Validate data quality against expected ranges and patterns."""
    
    def __init__(self, db_url: str, send_alerts: bool = False):
        """Initialize validator."""
        self.engine = create_engine(db_url)
        self.send_alerts = send_alerts
        self.webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL") if send_alerts else None
        self.validation_results = {}
    
    def validate_source(self, source: str) -> Dict:
        """
        Validate a single data source.
        
        Returns:
            Dict with validation results
        """
        print(f"\n{'='*60}")
        print(f"Validating {source}")
        print(f"{'='*60}")
        
        results = {
            "source": source,
            "passed": True,
            "issues": [],
            "warnings": []
        }
        
        with self.engine.connect() as conn:
            # Get data
            query = text("""
                SELECT date, value, variable_name
                FROM climate_data
                WHERE source = :source
                ORDER BY date DESC
                LIMIT 10000
            """)
            
            try:
                df = pd.read_sql(query, conn, params={"source": source})
                
                if df.empty:
                    results["passed"] = False
                    results["issues"].append("No data found")
                    print(f"✗ FAIL: No data available for {source}")
                    return results
                
                print(f"  Records analyzed: {len(df):,}")
                
                # Check for missing values
                null_pct = (df["value"].isnull().sum() / len(df)) * 100
                if null_pct > 10:
                    results["passed"] = False
                    results["issues"].append(f"{null_pct:.1f}% missing values (threshold: 10%)")
                    print(f"  ✗ {null_pct:.1f}% missing values")
                elif null_pct > 5:
                    results["warnings"].append(f"{null_pct:.1f}% missing values")
                    print(f"  ⚠ {null_pct:.1f}% missing values")
                else:
                    print(f"  ✓ Missing values: {null_pct:.2f}%")
                
                # Check data ranges
                valid_values = df["value"].dropna()
                if len(valid_values) > 0:
                    min_val = valid_values.min()
                    max_val = valid_values.max()
                    mean_val = valid_values.mean()
                    
                    print(f"  Range: [{min_val:.2f}, {max_val:.2f}], Mean: {mean_val:.2f}")
                    
                    # Validate against expected ranges (simplified check)
                    if min_val < -100 or max_val > 1000:
                        results["passed"] = False
                        results["issues"].append(f"Suspicious range: [{min_val:.2f}, {max_val:.2f}]")
                        print(f"  ✗ Suspicious data range")
                    else:
                        print(f"  ✓ Data range looks reasonable")
                    
                    # Check for outliers (values beyond 3 std devs)
                    std_dev = valid_values.std()
                    outliers = valid_values[(valid_values < mean_val - 3*std_dev) | 
                                          (valid_values > mean_val + 3*std_dev)]
                    outlier_pct = (len(outliers) / len(valid_values)) * 100
                    
                    if outlier_pct > 5:
                        results["warnings"].append(f"{outlier_pct:.1f}% outliers")
                        print(f"  ⚠ {outlier_pct:.1f}% outliers (3σ)")
                    else:
                        print(f"  ✓ Outliers: {outlier_pct:.2f}%")
                
                # Check temporal consistency
                if "date" in df.columns:
                    df_sorted = df.sort_values("date")
                    date_gaps = df_sorted["date"].diff()
                    large_gaps = date_gaps[date_gaps > pd.Timedelta(days=60)]
                    
                    if len(large_gaps) > 0:
                        results["warnings"].append(f"{len(large_gaps)} large temporal gaps")
                        print(f"  ⚠ {len(large_gaps)} gaps > 60 days")
                    else:
                        print(f"  ✓ No large temporal gaps")
                
                # Summary
                if results["passed"] and not results["warnings"]:
                    print(f"\n  ✓ PASS: {source} data quality is excellent")
                elif results["passed"]:
                    print(f"\n  ⚠ PASS (with warnings): {source} data quality is acceptable")
                else:
                    print(f"\n  ✗ FAIL: {source} has data quality issues")
                
                # Send alert if issues found and alerts enabled
                if self.send_alerts and (results["issues"] or len(results["warnings"]) > 2):
                    self._send_quality_alert(source, results, len(df))
            
            except Exception as e:
                results["passed"] = False
                results["issues"].append(f"Validation error: {str(e)}")
                print(f"  ✗ Error during validation: {e}")
        
        return results
    
    def _send_quality_alert(self, source: str, results: Dict, record_count: int):
        """Send data quality alert to Slack."""
        if not self.webhook_url:
            return
        
        issue_type = "Data Quality Issues" if results["issues"] else "Data Quality Warnings"
        details = "; ".join(results["issues"] + results["warnings"])
        severity = "critical" if results["issues"] else "warning"
        
        send_data_quality_alert(
            webhook_url=self.webhook_url,
            source=source,
            issue_type=issue_type,
            details=details,
            affected_records=record_count,
            severity=severity
        )
    
    def validate_all_sources(self) -> Dict:
        """Validate all data sources."""
        sources = ["CHIRPS", "NASA_POWER", "ERA5", "NDVI", "OCEAN_INDICES"]
        
        all_results = {}
        passed_count = 0
        
        for source in sources:
            results = self.validate_source(source)
            all_results[source] = results
            if results["passed"]:
                passed_count += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {passed_count}/{len(sources)} sources")
        
        for source, results in all_results.items():
            status = "✓ PASS" if results["passed"] else "✗ FAIL"
            issues_count = len(results["issues"]) + len(results["warnings"])
            print(f"{status:10} {source:20} ({issues_count} issues/warnings)")
        
        return all_results


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Validate data quality")
    parser.add_argument(
        "--source",
        type=str,
        choices=["CHIRPS", "NASA_POWER", "ERA5", "NDVI", "OCEAN_INDICES", "all"],
        default="all",
        help="Data source to validate"
    )
    parser.add_argument(
        "--send-alerts",
        action="store_true",
        help="Send Slack alerts for quality issues"
    )
    args = parser.parse_args()
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    # Run validation
    validator = DataQualityValidator(db_url, send_alerts=args.send_alerts)
    
    try:
        if args.source == "all":
            results = validator.validate_all_sources()
            all_passed = all(r["passed"] for r in results.values())
            sys.exit(0 if all_passed else 1)
        else:
            result = validator.validate_source(args.source)
            sys.exit(0 if result["passed"] else 1)
    
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
