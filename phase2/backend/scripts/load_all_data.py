"""
Master Data Loading Orchestration Script

Runs all data loaders in sequence to populate the dashboard database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import argparse
from datetime import datetime

# Import individual loaders
from load_climate_data import load_climate_data
from load_trigger_events import load_trigger_events
from load_model_metrics import load_model_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_all_data(clear_existing: bool = False, skip_models: bool = False):
    """
    Run all data loaders in sequence.
    
    Args:
        clear_existing: If True, clear all existing data before loading
        skip_models: If True, skip loading model metrics
    """
    logger.info("=" * 80)
    logger.info("DASHBOARD DATA LOADING - START")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Clear existing: {clear_existing}")
    logger.info(f"Skip models: {skip_models}")
    logger.info("")
    
    results = {
        'climate_data': False,
        'trigger_events': False,
        'model_metrics': False
    }
    
    # Step 1: Load climate data
    logger.info("=" * 80)
    logger.info("STEP 1: Loading Climate Data")
    logger.info("=" * 80)
    try:
        results['climate_data'] = load_climate_data(
            csv_path="/outputs/processed/master_dataset.csv",
            clear_existing=clear_existing
        )
        if results['climate_data']:
            logger.info("✓ Climate data loaded successfully\n")
        else:
            logger.error("✗ Climate data loading failed\n")
            return False
    except Exception as e:
        logger.error(f"✗ Climate data loading failed: {e}\n")
        return False
    
    # Step 2: Load trigger events
    logger.info("=" * 80)
    logger.info("STEP 2: Loading Trigger Events")
    logger.info("=" * 80)
    try:
        results['trigger_events'] = load_trigger_events(
            master_csv="/outputs/processed/master_dataset.csv",
            clear_existing=clear_existing
        )
        if results['trigger_events']:
            logger.info("✓ Trigger events loaded successfully\n")
        else:
            logger.error("✗ Trigger events loading failed\n")
            return False
    except Exception as e:
        logger.error(f"✗ Trigger events loading failed: {e}\n")
        return False
    
    # Step 3: Load model metrics
    if not skip_models:
        logger.info("=" * 80)
        logger.info("STEP 3: Loading Model Metrics")
        logger.info("=" * 80)
        try:
            results['model_metrics'] = load_model_metrics(
                results_file="outputs/models/training_results.json",
                clear_existing=clear_existing
            )
            if results['model_metrics']:
                logger.info("✓ Model metrics loaded successfully\n")
            else:
                logger.error("✗ Model metrics loading failed\n")
                return False
        except Exception as e:
            logger.error(f"✗ Model metrics loading failed: {e}\n")
            return False
    else:
        logger.info("Skipping model metrics loading (--skip-models flag set)\n")
        results['model_metrics'] = True
    
    # Final summary
    logger.info("=" * 80)
    logger.info("DATA LOADING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info("Summary:")
    logger.info(f"  ✓ Climate Data: {'SUCCESS' if results['climate_data'] else 'FAILED'}")
    logger.info(f"  ✓ Trigger Events: {'SUCCESS' if results['trigger_events'] else 'FAILED'}")
    logger.info(f"  ✓ Model Metrics: {'SUCCESS' if results['model_metrics'] else 'SKIPPED' if skip_models else 'FAILED'}")
    logger.info("")
    
    all_success = all(results.values())
    if all_success:
        logger.info("🎉 All data loaded successfully!")
    else:
        logger.error("❌ Some data loading steps failed")
    
    logger.info("=" * 80)
    
    return all_success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load all data into dashboard database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all data (keep existing)
  python load_all_data.py
  
  # Clear and reload all data
  python load_all_data.py --clear
  
  # Load only climate and trigger data
  python load_all_data.py --skip-models
  
  # Verify only (dry run)
  python load_all_data.py --verify-only
        """
    )
    
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing data before loading")
    parser.add_argument("--skip-models", action="store_true",
                       help="Skip loading model metrics")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify data, don't load")
    
    args = parser.parse_args()
    
    if args.verify_only:
        logger.info("Verification mode not yet implemented")
        sys.exit(0)
    
    success = load_all_data(
        clear_existing=args.clear,
        skip_models=args.skip_models
    )
    
    sys.exit(0 if success else 1)
