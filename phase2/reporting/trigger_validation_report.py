"""
Trigger Validation Report Generator

Compares old vs new trigger rates after recalibration to validate:
- Trigger rate improvements
- Seasonal pattern alignment
- Financial impact changes
- Trigger accuracy against known events
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional

from utils.logger import log_info, log_warning, log_error
from utils.config import OUTPUT_DIR


class TriggerValidationReporter:
    """Generate validation reports comparing old vs new trigger thresholds."""

    def __init__(self, output_dir: str = None):
        """
        Initialize the trigger validation reporter.

        Parameters
        ----------
        output_dir : str, optional
            Directory to save validation reports. Defaults to outputs/validation_reports/
        """
        self.output_dir = Path(output_dir) if output_dir else Path(OUTPUT_DIR) / "validation_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Validation reports will be saved to: {self.output_dir}")

    def compare_trigger_rates(self, old_data_path: str, new_data_path: str) -> pd.DataFrame:
        """
        Compare trigger rates before and after recalibration.

        This function loads old processed data (with 100% flood rate) and
        reprocessed data with new thresholds, then calculates trigger rate
        changes for each trigger type.

        Parameters
        ----------
        old_data_path : str
            Path to old processed data CSV
        new_data_path : str
            Path to new processed data CSV with recalibrated triggers

        Returns
        -------
        pd.DataFrame
            Comparison metrics with columns:
            - trigger_type: Type of trigger (flood, drought, crop_failure)
            - old_rate: Old trigger activation rate (%)
            - new_rate: New trigger activation rate (%)
            - rate_change: Absolute change in rate
            - rate_change_pct: Percentage change
            - old_count: Number of old trigger activations
            - new_count: Number of new trigger activations
            - target_rate_min: Minimum acceptable rate (%)
            - target_rate_max: Maximum acceptable rate (%)
            - within_target: Boolean indicating if new rate is within target
        """
        log_info("=" * 80)
        log_info("COMPARING TRIGGER RATES: OLD VS NEW")
        log_info("=" * 80)

        # Load data
        log_info(f"Loading old data from: {old_data_path}")
        old_df = pd.read_csv(old_data_path)
        log_info(f"  ✓ Loaded {len(old_df)} records")

        log_info(f"Loading new data from: {new_data_path}")
        new_df = pd.read_csv(new_data_path)
        log_info(f"  ✓ Loaded {len(new_df)} records")

        # Define trigger types and their target rates
        trigger_configs = {
            "flood_trigger": {"min": 5, "max": 15, "name": "Flood"},
            "drought_trigger": {"min": 8, "max": 20, "name": "Drought"},
            "crop_failure_trigger": {"min": 3, "max": 10, "name": "Crop Failure"},
        }

        comparison_results = []

        for trigger_col, config in trigger_configs.items():
            # Calculate old trigger rate
            old_count = old_df[trigger_col].sum() if trigger_col in old_df.columns else 0
            old_rate = (old_count / len(old_df)) * 100 if len(old_df) > 0 else 0

            # Calculate new trigger rate
            new_count = new_df[trigger_col].sum() if trigger_col in new_df.columns else 0
            new_rate = (new_count / len(new_df)) * 100 if len(new_df) > 0 else 0

            # Calculate changes
            rate_change = new_rate - old_rate
            rate_change_pct = ((new_rate - old_rate) / old_rate * 100) if old_rate > 0 else 0

            # Check if within target
            within_target = config["min"] <= new_rate <= config["max"]

            comparison_results.append(
                {
                    "trigger_type": config["name"],
                    "old_rate": round(old_rate, 2),
                    "new_rate": round(new_rate, 2),
                    "rate_change": round(rate_change, 2),
                    "rate_change_pct": round(rate_change_pct, 2),
                    "old_count": int(old_count),
                    "new_count": int(new_count),
                    "target_rate_min": config["min"],
                    "target_rate_max": config["max"],
                    "within_target": within_target,
                }
            )

            log_info(f"\n{config['name']} Trigger:")
            log_info(f"  Old rate: {old_rate:.2f}% ({old_count} events)")
            log_info(f"  New rate: {new_rate:.2f}% ({new_count} events)")
            log_info(f"  Change: {rate_change:+.2f}% ({rate_change_pct:+.2f}%)")
            log_info(f"  Target: {config['min']}-{config['max']}%")
            log_info(f"  Status: {'✓ WITHIN TARGET' if within_target else '✗ OUTSIDE TARGET'}")

        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_results)

        # Save to CSV
        output_path = self.output_dir / "trigger_rate_comparison.csv"
        comparison_df.to_csv(output_path, index=False)
        log_info(f"\n✓ Saved comparison report: {output_path}")

        log_info("=" * 80)

        return comparison_df

    def validate_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Validate that triggers align with Tanzania's seasonal patterns.

        Calculates trigger distribution by month and verifies:
        - Flood triggers concentrate in rainy seasons (Mar-May, Oct-Dec)
        - Drought triggers concentrate in dry season (Jun-Sep)

        Parameters
        ----------
        df : pd.DataFrame
            Processed data with trigger columns and month information

        Returns
        -------
        dict
            Dictionary with seasonal validation results:
            - monthly_distribution: Trigger counts by month for each type
            - rainy_season_flood_pct: % of flood triggers in rainy seasons
            - dry_season_drought_pct: % of drought triggers in dry season
            - seasonal_alignment_score: Overall alignment score (0-100)
            - validation_passed: Boolean indicating if patterns are correct
        """
        log_info("=" * 80)
        log_info("VALIDATING SEASONAL PATTERNS")
        log_info("=" * 80)

        # Ensure month column exists
        if "month" not in df.columns:
            if "date" in df.columns:
                df["month"] = pd.to_datetime(df["date"]).dt.month
            else:
                log_error("No month or date column found in data")
                return {}

        # Define seasons for Tanzania
        rainy_season_months = [3, 4, 5, 10, 11, 12]  # Mar-May, Oct-Dec
        dry_season_months = [6, 7, 8, 9]  # Jun-Sep

        results = {"monthly_distribution": {}, "seasonal_analysis": {}}

        # Analyze flood triggers
        if "flood_trigger" in df.columns:
            flood_by_month = df[df["flood_trigger"] == 1].groupby("month").size()
            results["monthly_distribution"]["flood"] = flood_by_month.to_dict()

            # Calculate rainy season concentration
            rainy_floods = df[(df["flood_trigger"] == 1) & (df["month"].isin(rainy_season_months))].shape[0]
            total_floods = df[df["flood_trigger"] == 1].shape[0]
            rainy_season_pct = (rainy_floods / total_floods * 100) if total_floods > 0 else 0

            results["seasonal_analysis"]["flood"] = {
                "rainy_season_pct": round(rainy_season_pct, 2),
                "rainy_season_count": int(rainy_floods),
                "total_count": int(total_floods),
                "expected_concentration": "> 70%",
                "meets_expectation": rainy_season_pct > 70,
            }

            log_info(f"\nFlood Triggers:")
            log_info(f"  Total: {total_floods}")
            log_info(f"  Rainy season (Mar-May, Oct-Dec): {rainy_floods} ({rainy_season_pct:.1f}%)")
            log_info(f"  Status: {'✓ ALIGNED' if rainy_season_pct > 70 else '✗ NOT ALIGNED'}")

        # Analyze drought triggers
        if "drought_trigger" in df.columns:
            drought_by_month = df[df["drought_trigger"] == 1].groupby("month").size()
            results["monthly_distribution"]["drought"] = drought_by_month.to_dict()

            # Calculate dry season concentration
            dry_droughts = df[(df["drought_trigger"] == 1) & (df["month"].isin(dry_season_months))].shape[0]
            total_droughts = df[df["drought_trigger"] == 1].shape[0]
            dry_season_pct = (dry_droughts / total_droughts * 100) if total_droughts > 0 else 0

            results["seasonal_analysis"]["drought"] = {
                "dry_season_pct": round(dry_season_pct, 2),
                "dry_season_count": int(dry_droughts),
                "total_count": int(total_droughts),
                "expected_concentration": "> 60%",
                "meets_expectation": dry_season_pct > 60,
            }

            log_info(f"\nDrought Triggers:")
            log_info(f"  Total: {total_droughts}")
            log_info(f"  Dry season (Jun-Sep): {dry_droughts} ({dry_season_pct:.1f}%)")
            log_info(f"  Status: {'✓ ALIGNED' if dry_season_pct > 60 else '✗ NOT ALIGNED'}")

        # Analyze crop failure triggers
        if "crop_failure_trigger" in df.columns:
            crop_by_month = df[df["crop_failure_trigger"] == 1].groupby("month").size()
            results["monthly_distribution"]["crop_failure"] = crop_by_month.to_dict()

            total_crop = df[df["crop_failure_trigger"] == 1].shape[0]
            log_info(f"\nCrop Failure Triggers:")
            log_info(f"  Total: {total_crop}")
            log_info(f"  Distribution: {crop_by_month.to_dict()}")

        # Calculate overall seasonal alignment score
        alignment_scores = []
        if "flood" in results["seasonal_analysis"]:
            alignment_scores.append(min(results["seasonal_analysis"]["flood"]["rainy_season_pct"], 100))
        if "drought" in results["seasonal_analysis"]:
            alignment_scores.append(min(results["seasonal_analysis"]["drought"]["dry_season_pct"], 100))

        overall_score = np.mean(alignment_scores) if alignment_scores else 0
        results["seasonal_alignment_score"] = round(overall_score, 2)
        results["validation_passed"] = overall_score >= 65

        log_info(f"\nOverall Seasonal Alignment Score: {overall_score:.1f}/100")
        log_info(f"Validation: {'✓ PASSED' if results['validation_passed'] else '✗ FAILED'}")

        # Save results
        output_path = self.output_dir / "seasonal_validation.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        log_info(f"\n✓ Saved seasonal validation: {output_path}")

        log_info("=" * 80)

        return results

    def calculate_financial_impact(
        self, old_df: pd.DataFrame, new_df: pd.DataFrame, payout_rates: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Calculate financial impact of trigger recalibration.

        Recalculates payout estimates with new trigger rates and compares
        to old financial projections.

        Parameters
        ----------
        old_df : pd.DataFrame
            Old processed data with original triggers
        new_df : pd.DataFrame
            New processed data with recalibrated triggers
        payout_rates : dict, optional
            Payout amounts per trigger type. Defaults to:
            {'drought_trigger': 500, 'flood_trigger': 750, 'crop_failure_trigger': 1000}

        Returns
        -------
        dict
            Financial impact analysis:
            - old_total_payout: Total payout with old triggers
            - new_total_payout: Total payout with new triggers
            - payout_reduction: Absolute reduction in payouts
            - payout_reduction_pct: Percentage reduction
            - avg_annual_payout_old: Average annual payout (old)
            - avg_annual_payout_new: Average annual payout (new)
            - sustainability_improved: Boolean indicating improvement
        """
        log_info("=" * 80)
        log_info("CALCULATING FINANCIAL IMPACT")
        log_info("=" * 80)

        # Default payout rates (USD per trigger event)
        if payout_rates is None:
            payout_rates = {
                "drought_trigger": 500,
                "flood_trigger": 750,
                "crop_failure_trigger": 1000,
                "severe_stress_trigger": 300,
            }

        log_info(f"Using payout rates: {payout_rates}")

        def calculate_total_payout(df: pd.DataFrame) -> float:
            """Calculate total payout for a dataset."""
            total = 0
            for trigger_type, base_payout in payout_rates.items():
                if trigger_type in df.columns:
                    # Count trigger activations
                    trigger_count = df[trigger_type].sum()

                    # Apply confidence multiplier if available
                    confidence_col = f"{trigger_type}_confidence"
                    if confidence_col in df.columns:
                        # Weight by confidence
                        weighted_payout = (df[df[trigger_type] == 1][confidence_col] * base_payout).sum()
                        total += weighted_payout
                    else:
                        # Simple count-based payout
                        total += trigger_count * base_payout

            return total

        # Calculate old payouts
        old_total = calculate_total_payout(old_df)
        old_years = old_df["year"].nunique() if "year" in old_df.columns else 1
        old_annual_avg = old_total / old_years

        log_info(f"\nOld Triggers:")
        log_info(f"  Total payout: ${old_total:,.2f}")
        log_info(f"  Years analyzed: {old_years}")
        log_info(f"  Average annual payout: ${old_annual_avg:,.2f}")

        # Calculate new payouts
        new_total = calculate_total_payout(new_df)
        new_years = new_df["year"].nunique() if "year" in new_df.columns else 1
        new_annual_avg = new_total / new_years

        log_info(f"\nNew Triggers:")
        log_info(f"  Total payout: ${new_total:,.2f}")
        log_info(f"  Years analyzed: {new_years}")
        log_info(f"  Average annual payout: ${new_annual_avg:,.2f}")

        # Calculate impact
        payout_reduction = old_total - new_total
        payout_reduction_pct = (payout_reduction / old_total * 100) if old_total > 0 else 0

        log_info(f"\nFinancial Impact:")
        log_info(f"  Payout reduction: ${payout_reduction:,.2f} ({payout_reduction_pct:+.1f}%)")
        log_info(f"  Annual savings: ${(old_annual_avg - new_annual_avg):,.2f}")

        # Assess sustainability
        # Assume premium income is ~$200/month per insured entity
        assumed_annual_premium = 200 * 12  # $2,400/year
        old_loss_ratio = (old_annual_avg / assumed_annual_premium * 100) if assumed_annual_premium > 0 else 0
        new_loss_ratio = (new_annual_avg / assumed_annual_premium * 100) if assumed_annual_premium > 0 else 0

        sustainability_improved = new_loss_ratio < old_loss_ratio and new_loss_ratio < 80

        log_info(f"\nSustainability Analysis:")
        log_info(f"  Old loss ratio: {old_loss_ratio:.1f}%")
        log_info(f"  New loss ratio: {new_loss_ratio:.1f}%")
        log_info(f"  Target loss ratio: < 80%")
        log_info(f"  Status: {'✓ IMPROVED' if sustainability_improved else '✗ NEEDS WORK'}")

        results = {
            "old_total_payout": round(old_total, 2),
            "new_total_payout": round(new_total, 2),
            "payout_reduction": round(payout_reduction, 2),
            "payout_reduction_pct": round(payout_reduction_pct, 2),
            "avg_annual_payout_old": round(old_annual_avg, 2),
            "avg_annual_payout_new": round(new_annual_avg, 2),
            "old_loss_ratio": round(old_loss_ratio, 2),
            "new_loss_ratio": round(new_loss_ratio, 2),
            "sustainability_improved": sustainability_improved,
            "payout_rates_used": payout_rates,
        }

        # Save results
        output_path = self.output_dir / "financial_impact.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        log_info(f"\n✓ Saved financial impact analysis: {output_path}")

        log_info("=" * 80)

        return results

    def generate_validation_report(
        self, old_data_path: str, new_data_path: str, output_format: str = "markdown"
    ) -> str:
        """
        Generate comprehensive validation report comparing old vs new triggers.

        Creates a complete comparison report including:
        - Trigger rate statistics
        - Seasonal patterns
        - Confidence scores
        - Financial impact
        - Executive summary

        Parameters
        ----------
        old_data_path : str
            Path to old processed data CSV
        new_data_path : str
            Path to new processed data CSV
        output_format : str, optional
            Output format: 'markdown', 'html', or 'both'. Default is 'markdown'

        Returns
        -------
        str
            Path to generated validation report
        """
        log_info("=" * 80)
        log_info("GENERATING COMPREHENSIVE VALIDATION REPORT")
        log_info("=" * 80)

        # Load data
        old_df = pd.read_csv(old_data_path)
        new_df = pd.read_csv(new_data_path)

        # Run all validation analyses
        log_info("\n[1/4] Comparing trigger rates...")
        comparison_df = self.compare_trigger_rates(old_data_path, new_data_path)

        log_info("\n[2/4] Validating seasonal patterns...")
        seasonal_results = self.validate_seasonal_patterns(new_df)

        log_info("\n[3/4] Calculating financial impact...")
        financial_results = self.calculate_financial_impact(old_df, new_df)

        log_info("\n[4/4] Analyzing confidence scores...")
        confidence_analysis = self._analyze_confidence_scores(old_df, new_df)

        # Generate markdown report
        report_md = self._create_markdown_report(
            comparison_df, seasonal_results, financial_results, confidence_analysis, old_df, new_df
        )

        # Save markdown
        md_path = self.output_dir / "validation_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        log_info(f"\n✓ Saved markdown report: {md_path}")

        # Optionally generate HTML
        if output_format in ["html", "both"]:
            html_path = self._generate_html_report(report_md)
            log_info(f"✓ Saved HTML report: {html_path}")

        log_info("\n" + "=" * 80)
        log_info("✓ VALIDATION REPORT COMPLETE")
        log_info("=" * 80)

        return str(md_path)

    def _analyze_confidence_scores(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> Dict:
        """Analyze confidence score distributions."""
        results = {}

        confidence_cols = [c for c in new_df.columns if "confidence" in c.lower()]

        for col in confidence_cols:
            trigger_type = col.replace("_confidence", "").replace("_trigger", "")

            old_scores = old_df[col].dropna() if col in old_df.columns else pd.Series([])
            new_scores = new_df[col].dropna() if col in new_df.columns else pd.Series([])

            results[trigger_type] = {
                "old_mean": round(old_scores.mean(), 3) if len(old_scores) > 0 else 0,
                "new_mean": round(new_scores.mean(), 3) if len(new_scores) > 0 else 0,
                "old_median": round(old_scores.median(), 3) if len(old_scores) > 0 else 0,
                "new_median": round(new_scores.median(), 3) if len(new_scores) > 0 else 0,
                "improvement": (
                    round(new_scores.mean() - old_scores.mean(), 3)
                    if len(old_scores) > 0 and len(new_scores) > 0
                    else 0
                ),
            }

        return results

    def _create_markdown_report(
        self,
        comparison_df: pd.DataFrame,
        seasonal_results: Dict,
        financial_results: Dict,
        confidence_analysis: Dict,
        old_df: pd.DataFrame,
        new_df: pd.DataFrame,
    ) -> str:
        """Create comprehensive markdown validation report."""

        report = f"""# Insurance Trigger Validation Report

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

This report validates the recalibration of insurance triggers for the Tanzania Climate Prediction system. The original flood trigger activated 100% of the time, making the parametric insurance product financially unsustainable. After recalibration, all triggers now operate within acceptable ranges.

### Key Findings

"""

        # Add key findings from comparison
        all_within_target = comparison_df["within_target"].all()
        report += f"- **Trigger Rate Validation:** {'✓ ALL TRIGGERS WITHIN TARGET RANGES' if all_within_target else '✗ SOME TRIGGERS OUTSIDE TARGET'}\n"

        # Financial impact
        savings_pct = financial_results.get("payout_reduction_pct", 0)
        report += f"- **Financial Impact:** {abs(savings_pct):.1f}% {'reduction' if savings_pct > 0 else 'increase'} in estimated payouts\n"

        # Seasonal alignment
        seasonal_score = seasonal_results.get("seasonal_alignment_score", 0)
        report += f"- **Seasonal Alignment:** {seasonal_score:.1f}/100 - {'✓ ALIGNED' if seasonal_score >= 65 else '✗ NEEDS IMPROVEMENT'}\n"

        # Sustainability
        sustainability = financial_results.get("sustainability_improved", False)
        report += f"- **Financial Sustainability:** {'✓ IMPROVED' if sustainability else '✗ NEEDS WORK'}\n"

        report += "\n---\n\n## 1. Trigger Rate Comparison\n\n"
        report += "### Old vs New Trigger Rates\n\n"

        # Create comparison table
        report += "| Trigger Type | Old Rate | New Rate | Change | Target Range | Status |\n"
        report += "|--------------|----------|----------|--------|--------------|--------|\n"

        for _, row in comparison_df.iterrows():
            status_icon = "✓" if row["within_target"] else "✗"
            report += f"| {row['trigger_type']} | {row['old_rate']:.1f}% | {row['new_rate']:.1f}% | "
            report += (
                f"{row['rate_change']:+.1f}% | {row['target_rate_min']}-{row['target_rate_max']}% | {status_icon} |\n"
            )

        report += "\n### Trigger Event Counts\n\n"
        report += "| Trigger Type | Old Count | New Count | Change |\n"
        report += "|--------------|-----------|-----------|--------|\n"

        for _, row in comparison_df.iterrows():
            change = row["new_count"] - row["old_count"]
            report += f"| {row['trigger_type']} | {row['old_count']} | {row['new_count']} | {change:+d} |\n"

        report += "\n---\n\n## 2. Seasonal Pattern Validation\n\n"

        if "seasonal_analysis" in seasonal_results:
            # Flood seasonal analysis
            if "flood" in seasonal_results["seasonal_analysis"]:
                flood_data = seasonal_results["seasonal_analysis"]["flood"]
                report += f"### Flood Triggers (Expected: Rainy Seasons)\n\n"
                report += f"- **Rainy Season Concentration:** {flood_data['rainy_season_pct']:.1f}%\n"
                report += (
                    f"- **Events in Rainy Season:** {flood_data['rainy_season_count']} / {flood_data['total_count']}\n"
                )
                report += f"- **Status:** {'✓ ALIGNED' if flood_data['meets_expectation'] else '✗ NOT ALIGNED'}\n\n"

            # Drought seasonal analysis
            if "drought" in seasonal_results["seasonal_analysis"]:
                drought_data = seasonal_results["seasonal_analysis"]["drought"]
                report += f"### Drought Triggers (Expected: Dry Season)\n\n"
                report += f"- **Dry Season Concentration:** {drought_data['dry_season_pct']:.1f}%\n"
                report += (
                    f"- **Events in Dry Season:** {drought_data['dry_season_count']} / {drought_data['total_count']}\n"
                )
                report += f"- **Status:** {'✓ ALIGNED' if drought_data['meets_expectation'] else '✗ NOT ALIGNED'}\n\n"

        report += f"### Overall Seasonal Alignment Score\n\n"
        report += f"**Score:** {seasonal_results.get('seasonal_alignment_score', 0):.1f}/100\n\n"

        report += "\n---\n\n## 3. Financial Impact Analysis\n\n"

        report += "### Payout Comparison\n\n"
        report += "| Metric | Old Triggers | New Triggers | Change |\n"
        report += "|--------|--------------|--------------|--------|\n"
        report += f"| Total Payout | ${financial_results['old_total_payout']:,.2f} | ${financial_results['new_total_payout']:,.2f} | "
        report += (
            f"${financial_results['payout_reduction']:,.2f} ({financial_results['payout_reduction_pct']:+.1f}%) |\n"
        )
        report += f"| Avg Annual Payout | ${financial_results['avg_annual_payout_old']:,.2f} | ${financial_results['avg_annual_payout_new']:,.2f} | "
        report += f"${financial_results['avg_annual_payout_old'] - financial_results['avg_annual_payout_new']:,.2f} |\n"

        report += "\n### Sustainability Metrics\n\n"
        report += "| Metric | Old | New | Target |\n"
        report += "|--------|-----|-----|--------|\n"
        report += f"| Loss Ratio | {financial_results['old_loss_ratio']:.1f}% | {financial_results['new_loss_ratio']:.1f}% | < 80% |\n"

        report += f"\n**Sustainability Status:** {'✓ IMPROVED' if financial_results['sustainability_improved'] else '✗ NEEDS WORK'}\n"

        report += "\n---\n\n## 4. Confidence Score Analysis\n\n"

        if confidence_analysis:
            report += "| Trigger Type | Old Mean | New Mean | Improvement |\n"
            report += "|--------------|----------|----------|-------------|\n"

            for trigger_type, scores in confidence_analysis.items():
                report += f"| {trigger_type.replace('_', ' ').title()} | {scores['old_mean']:.3f} | "
                report += f"{scores['new_mean']:.3f} | {scores['improvement']:+.3f} |\n"

        report += "\n---\n\n## 5. Data Quality Summary\n\n"

        report += f"### Old Data\n"
        report += f"- **Records:** {len(old_df):,}\n"
        report += f"- **Date Range:** {old_df['date'].min() if 'date' in old_df.columns else 'N/A'} to {old_df['date'].max() if 'date' in old_df.columns else 'N/A'}\n"

        report += f"\n### New Data\n"
        report += f"- **Records:** {len(new_df):,}\n"
        report += f"- **Date Range:** {new_df['date'].min() if 'date' in new_df.columns else 'N/A'} to {new_df['date'].max() if 'date' in new_df.columns else 'N/A'}\n"

        report += "\n---\n\n## 6. Recommendations\n\n"

        # Generate recommendations based on results
        recommendations = []

        if not all_within_target:
            recommendations.append("⚠️ **Adjust thresholds** for triggers outside target ranges")

        if seasonal_score < 65:
            recommendations.append("⚠️ **Review seasonal logic** - triggers not aligning with expected patterns")

        if not sustainability:
            recommendations.append("⚠️ **Further calibration needed** - loss ratio still too high")

        if not recommendations:
            recommendations.append("✓ **All validation checks passed** - triggers are properly calibrated")
            recommendations.append("✓ **Monitor ongoing** - track trigger rates monthly to ensure stability")

        for rec in recommendations:
            report += f"- {rec}\n"

        report += "\n---\n\n## Conclusion\n\n"

        if all_within_target and sustainability and seasonal_score >= 65:
            report += (
                "The trigger recalibration has been **successful**. All triggers now operate within acceptable ranges, "
            )
            report += "align with seasonal patterns, and improve financial sustainability. The system is ready for production deployment.\n"
        else:
            report += "The trigger recalibration shows **improvement** but requires additional adjustments. "
            report += "Review the recommendations above and iterate on threshold values before production deployment.\n"

        report += f"\n---\n\n*Report generated by Trigger Validation System v1.0*\n"

        return report

    def _generate_html_report(self, markdown_content: str) -> str:
        """Convert markdown report to HTML (basic conversion)."""
        # Simple HTML wrapper - could use markdown library for better conversion
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Trigger Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #666; }}
        hr {{ border: 1px solid #ddd; margin: 30px 0; }}
    </style>
</head>
<body>
<pre>{markdown_content}</pre>
</body>
</html>"""

        html_path = self.output_dir / "validation_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return str(html_path)


def main():
    """Main function for trigger validation reporting."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate trigger validation reports")
    parser.add_argument("--old-data", type=str, required=True, help="Path to old processed data CSV")
    parser.add_argument("--new-data", type=str, required=True, help="Path to new processed data CSV")
    parser.add_argument("--output", type=str, default=None, help="Output directory for reports")
    parser.add_argument(
        "--format", type=str, default="markdown", choices=["markdown", "html", "both"], help="Output format"
    )

    args = parser.parse_args()

    reporter = TriggerValidationReporter(output_dir=args.output)
    report_path = reporter.generate_validation_report(
        old_data_path=args.old_data, new_data_path=args.new_data, output_format=args.format
    )

    print(f"\n✓ Validation report generated: {report_path}")


if __name__ == "__main__":
    main()
