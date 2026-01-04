"""
Insurance Business Pipeline Orchestrator

Comprehensive workflow for generating insurance business reports and analytics.
This pipeline coordinates:
    1. Data loading (6-location master dataset)
    2. Rule-based insurance trigger evaluation
    3. Payout calculations (TZS)
    4. Business report generation
    5. Visualization creation
    6. Experiment tracking

Usage:
    # Generate reports with default settings
    python pipelines/insurance_business_pipeline.py
    
    # Specify custom data path
    python pipelines/insurance_business_pipeline.py --input data/custom_dataset.csv
    
    # Skip visualizations
    python pipelines/insurance_business_pipeline.py --skip-visualizations
    
    # Force trigger recalibration
    python pipelines/insurance_business_pipeline.py --recalibrate
"""

import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from reporting.business_metrics import BusinessMetricsReporter
from reporting.visualize_business_metrics import BusinessMetricsVisualizer
from utils.logger import get_logger, log_info, log_warning, log_error

# Setup logger
logger = get_logger(__name__)


def run_insurance_business_pipeline(
    input_path: str = "data/processed/master_dataset.csv",
    output_dir: str = "outputs/business_reports",
    skip_visualizations: bool = False,
    recalibrate_triggers: bool = False,
) -> Dict[str, Any]:
    """
    Execute complete insurance business reporting workflow.
    
    This pipeline orchestrates the generation of parametric insurance
    business reports from rule-based triggers on climate data.
    
    Parameters
    ----------
    input_path : str
        Path to master dataset with 6-location data
    output_dir : str
        Directory for output reports
    skip_visualizations : bool
        Skip visualization generation
    recalibrate_triggers : bool
        Force recalibration of trigger thresholds
        
    Returns
    -------
    dict
        Summary of pipeline execution results
    """
    
    pipeline_start = time.time()
    
    logger.info("=" * 80)
    logger.info("INSURANCE BUSINESS PIPELINE - 6-LOCATION SYSTEM")
    logger.info("=" * 80)
    logger.info(f"Input data: {input_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Visualizations: {'Disabled' if skip_visualizations else 'Enabled'}")
    logger.info(f"Trigger recalibration: {'Enabled' if recalibrate_triggers else 'Disabled'}")
    logger.info("=" * 80)
    
    results = {
        "pipeline_name": "insurance_business_pipeline",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_path": input_path,
        "output_dir": output_dir,
        "steps_completed": [],
        "errors": []
    }
    
    try:
        # =================================================================
        # STEP 1: SMART DATA LOADING & VALIDATION
        # =================================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: SMART DATA LOADING & VALIDATION")
        logger.info("=" * 80)
        
        input_file = Path(input_path)
        df = None
        data_source = None
        
        # Option A: User-specified input exists
        if input_file.exists():
            logger.info(f"Loading data from: {input_path}")
            df = pd.read_csv(input_path)
            data_source = "user_specified"
            logger.info(f"✓ Loaded {len(df):,} records from {input_file.name}")
        
        # Option B: Auto-detect and combine train/val/test splits
        else:
            logger.warning(f"Input file not found: {input_path}")
            logger.info("Attempting auto-detection of train/val/test splits...")
            
            # Check for feature splits
            splits_dir = Path("outputs/processed")
            train_file = splits_dir / "features_train.csv"
            val_file = splits_dir / "features_val.csv"
            test_file = splits_dir / "features_test.csv"
            
            if train_file.exists() and val_file.exists() and test_file.exists():
                logger.info("✓ Found train/val/test splits - combining automatically...")
                
                train = pd.read_csv(train_file)
                val = pd.read_csv(val_file)
                test = pd.read_csv(test_file)
                
                logger.info(f"  Train: {len(train):,} records")
                logger.info(f"  Val:   {len(val):,} records")
                logger.info(f"  Test:  {len(test):,} records")
                
                df = pd.concat([train, val, test], ignore_index=True)
                data_source = "auto_combined"
                
                logger.info(f"✓ Combined dataset: {len(df):,} records")
                
                # Save for future runs (optimization)
                master_path = Path(input_path)
                master_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(master_path, index=False)
                logger.info(f"✓ Saved master dataset to: {master_path}")
                logger.info("  (Future runs will use this cached file)")
                
            else:
                # Option C: No data found
                raise FileNotFoundError(
                    f"\n❌ No data found!\n\n"
                    f"Searched for:\n"
                    f"  1. {input_path} (not found)\n"
                    f"  2. {train_file} (not found)\n\n"
                    f"Please run one of:\n"
                    f"  1. Data processing pipeline: python modules/processing/orchestrator.py\n"
                    f"  2. ML training pipeline: python pipelines/model_development_pipeline.py\n"
                    f"  3. Or provide custom data: --input path/to/your/data.csv\n"
                )
        
        # Validate data structure
        required_cols = ["year", "month"]
        trigger_cols = [c for c in df.columns if "trigger" in c.lower()]
        
        logger.info(f"\n📊 Dataset Validation:")
        logger.info(f"  Total records: {len(df):,}")
        logger.info(f"  Total columns: {len(df.columns)}")
        logger.info(f"  Data source: {data_source}")
        
        if not trigger_cols:
            logger.warning("  ⚠️  No trigger columns found - triggers may need to be calculated")
        else:
            logger.info(f"  ✓ Found {len(trigger_cols)} trigger columns")
            # Log first few trigger columns
            logger.info(f"    Examples: {', '.join(trigger_cols[:5])}")
        
        # Check for multi-location data
        if "location" in df.columns:
            locations = df["location"].nunique()
            logger.info(f"  ✓ Multi-location dataset: {locations} locations")
            logger.info(f"    Locations: {', '.join(df['location'].unique()[:10])}")
            results["locations_count"] = int(locations)
            results["location_names"] = df["location"].unique().tolist()
        else:
            logger.info("  ℹ️  Single-location dataset")
            results["locations_count"] = 1
        
        # Date range
        if "year" in df.columns and "month" in df.columns:
            date_start = f"{df['year'].min()}-{df['month'].min():02d}"
            date_end = f"{df['year'].max()}-{df['month'].max():02d}"
            logger.info(f"  ✓ Date range: {date_start} to {date_end}")
            results["date_range"] = {"start": date_start, "end": date_end}
        
        results["total_records"] = len(df)
        results["trigger_count"] = len(trigger_cols)
        results["data_source"] = data_source
        results["steps_completed"].append("data_validation")
        
        # =================================================================
        # STEP 2: (OPTIONAL) TRIGGER RECALIBRATION
        # =================================================================
        if recalibrate_triggers:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: TRIGGER THRESHOLD RECALIBRATION")
            logger.info("=" * 80)
            logger.warning("Trigger recalibration not yet implemented")
            logger.info("  Using existing trigger values in dataset")
            # TODO: Integrate modules/calibration/calibrate_triggers.py
            results["steps_completed"].append("trigger_recalibration_skipped")
        else:
            logger.info("\n✓ Using existing trigger values (skip recalibration)")
        
        # =================================================================
        # STEP 3: GENERATE BUSINESS REPORTS
        # =================================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: GENERATE BUSINESS REPORTS")
        logger.info("=" * 80)
        
        reporter = BusinessMetricsReporter(output_dir=output_dir)
        report_results = reporter.generate_full_report(data_path=input_path)
        
        results["reports_generated"] = report_results
        results["steps_completed"].append("business_reports")
        
        # =================================================================
        # STEP 4: GENERATE VISUALIZATIONS
        # =================================================================
        if not skip_visualizations:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: GENERATE VISUALIZATIONS")
            logger.info("=" * 80)
            
            try:
                visualizer = BusinessMetricsVisualizer(reports_dir=output_dir)
                visualizer.generate_all_visualizations()
                
                viz_dir = Path(output_dir) / "visualizations"
                viz_files = list(viz_dir.glob("*.png")) if viz_dir.exists() else []
                
                results["visualizations"] = {
                    "count": len(viz_files),
                    "files": [f.name for f in viz_files]
                }
                results["steps_completed"].append("visualizations")
                
                logger.info(f"✓ Generated {len(viz_files)} visualizations")
                
            except Exception as e:
                logger.error(f"Visualization generation failed: {e}")
                results["errors"].append(f"Visualization error: {str(e)}")
                results["visualizations"] = {"count": 0, "error": str(e)}
        else:
            logger.info("\n[OK] Skipping visualizations (as requested)")
            results["visualizations"] = {"count": 0, "skipped": True}
        
        # =================================================================
        # STEP 5: SUMMARY STATISTICS
        # =================================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: PIPELINE SUMMARY")
        logger.info("=" * 80)
        
        # Calculate key metrics
        if trigger_cols:
            for trigger in trigger_cols:
                if trigger in df.columns:
                    count = int(df[trigger].sum())
                    rate = (count / len(df) * 100) if len(df) > 0 else 0
                    logger.info(f"  {trigger}: {count} events ({rate:.2f}%)")
        
        # Calculate execution time
        pipeline_duration = time.time() - pipeline_start
        results["duration_seconds"] = round(pipeline_duration, 2)
        results["duration_minutes"] = round(pipeline_duration / 60, 2)
        
        logger.info(f"\n✓ Pipeline duration: {pipeline_duration:.2f} seconds ({pipeline_duration/60:.2f} minutes)")
        
        # =================================================================
        # FINAL STATUS
        # =================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Reports generated: {len(results.get('reports_generated', {}))} types")
        logger.info(f"Visualizations: {results.get('visualizations', {}).get('count', 0)}")
        logger.info(f"Total records processed: {results['total_records']:,}")
        logger.info(f"Locations covered: {results.get('locations_count', 1)}")
        logger.info("=" * 80)
        
        results["status"] = "SUCCESS"
        return results
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("PIPELINE FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        
        results["status"] = "FAILED"
        results["error"] = str(e)
        results["errors"].append(str(e))
        
        raise


def main():
    """Command-line interface for insurance business pipeline."""
    
    parser = argparse.ArgumentParser(
        description="Insurance Business Pipeline - Generate parametric insurance reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python pipelines/insurance_business_pipeline.py
  
  # Custom data path
  python pipelines/insurance_business_pipeline.py --input data/my_dataset.csv
  
  # Skip visualizations (faster)
  python pipelines/insurance_business_pipeline.py --skip-visualizations
  
  # Force trigger recalibration
  python pipelines/insurance_business_pipeline.py --recalibrate
        """
    )
    
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/master_dataset.csv",
        help="Path to input dataset (default: data/processed/master_dataset.csv)"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/business_reports",
        help="Output directory for reports (default: outputs/business_reports)"
    )
    
    parser.add_argument(
        "--skip-visualizations",
        action="store_true",
        help="Skip generation of visualizations (faster execution)"
    )
    
    parser.add_argument(
        "--recalibrate",
        action="store_true",
        help="Force recalibration of trigger thresholds before generating reports"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    try:
        # Run pipeline
        results = run_insurance_business_pipeline(
            input_path=args.input,
            output_dir=args.output,
            skip_visualizations=args.skip_visualizations,
            recalibrate_triggers=args.recalibrate
        )
        
        # Exit with success
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\nPipeline failed with error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
