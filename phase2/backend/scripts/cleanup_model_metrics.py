"""
Database cleanup script to fix duplicate models and missing metadata in model_metrics table.

This script:
1. Identifies duplicate model records based on normalized names
2. Keeps only the most recent record for each unique model
3. Adds missing metadata (dates, experiment IDs)
4. Supports dry-run mode for safety

Usage:
    # Preview changes without applying
    python cleanup_model_metrics.py --dry-run
    
    # Apply cleanup
    python cleanup_model_metrics.py
"""

import sys
import os
from datetime import datetime, date
from sqlalchemy import func
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.database import SessionLocal
    from app.models.model_metric import ModelMetric
except ImportError:
    # Try alternate path for Docker
    sys.path.append("/app")
    from app.core.database import SessionLocal
    from app.models.model_metric import ModelMetric

import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def normalize_model_name(name: str) -> str:
    """Normalize model name to lowercase with underscores."""
    return name.lower().replace(' ', '_').replace('-', '_')


def get_standardized_name(normalized_name: str) -> str:
    """Map normalized names to standardized canonical names."""
    # Mapping of variations to canonical names
    name_map = {
        'ensemble': 'ensemble',
        'xgboost': 'xgboost',
        'xgb': 'xgboost',
        'lstm': 'lstm',
        'random_forest': 'random_forest',
        'randomforest': 'random_forest',
        'rf': 'random_forest',
        'ridge': 'ridge',
        'ridge_regression': 'ridge',
        'random_forest_climate': 'random_forest',
        'xgboost_climate': 'xgboost'
    }
    
    return name_map.get(normalized_name, normalized_name)


def find_duplicates(db) -> Dict[str, List[ModelMetric]]:
    """Find all duplicate model records grouped by standardized name."""
    all_metrics = db.query(ModelMetric).all()
    
    # Group by standardized name
    grouped: Dict[str, List[ModelMetric]] = {}
    for metric in all_metrics:
        normalized = normalize_model_name(metric.model_name)
        standardized = get_standardized_name(normalized)
        
        if standardized not in grouped:
            grouped[standardized] = []
        grouped[standardized].append(metric)
    
    # Filter to only duplicates
    duplicates = {name: records for name, records in grouped.items() if len(records) > 1}
    
    return duplicates


def cleanup_duplicates(db, dry_run: bool = True) -> Tuple[int, int]:
    """
    Remove duplicate model records, keeping the most recent one.
    
    Returns:
        Tuple of (records_kept, records_deleted)
    """
    duplicates = find_duplicates(db)
    
    if not duplicates:
        logger.info("✅ No duplicates found!")
        return 0, 0
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Found {len(duplicates)} models with duplicates")
    logger.info(f"{'='*60}\n")
    
    records_kept = 0
    records_deleted = 0
    
    for standardized_name, records in duplicates.items():
        logger.info(f"\n📊 Model: {standardized_name}")
        logger.info(f"   Found {len(records)} duplicate records:")
        
        # Sort by most recent first (by id as tiebreaker for same training_date)
        sorted_records = sorted(
            records,
            key=lambda r: (r.training_date or datetime.min, r.id),
            reverse=True
        )
        
        # Keep the first (most recent)
        keep = sorted_records[0]
        delete_records = sorted_records[1:]
        
        logger.info(f"   ✅ KEEP:   ID={keep.id}, name='{keep.model_name}', "
                   f"training_date={keep.training_date}, r2={keep.r2_score}")
        
        for record in delete_records:
            logger.info(f"   ❌ DELETE: ID={record.id}, name='{record.model_name}', "
                       f"training_date={record.training_date}, r2={record.r2_score}")
            
            if not dry_run:
                db.delete(record)
                records_deleted += 1
        
        # Update the kept record to use standardized name
        old_name = keep.model_name
        if keep.model_name != standardized_name:
            logger.info(f"   🔄 Rename: '{old_name}' → '{standardized_name}'")
            if not dry_run:
                keep.model_name = standardized_name
        
        records_kept += 1
    
    if not dry_run:
        db.commit()
        logger.info(f"\n✅ Cleanup committed to database")
    else:
        logger.info(f"\n⚠️  DRY RUN - No changes made (use without --dry-run to apply)")
    
    return records_kept, records_deleted


def add_missing_metadata(db, dry_run: bool = True) -> int:
    """Add missing metadata to model records."""
    logger.info(f"\n{'='*60}")
    logger.info("Adding missing metadata")
    logger.info(f"{'='*60}\n")
    
    # Get all records
    all_metrics = db.query(ModelMetric).all()
    updated_count = 0
    
    # Default date range for training data
    default_start_date = date(2015, 1, 1)
    default_end_date = date(2025, 12, 31)
    
    for metric in all_metrics:
        updates = []
        
        if metric.data_start_date is None:
            metric.data_start_date = default_start_date
            updates.append("data_start_date")
        
        if metric.data_end_date is None:
            metric.data_end_date = default_end_date
            updates.append("data_end_date")
        
        if metric.experiment_id is None:
            metric.experiment_id = f"{metric.model_name}_baseline"
            updates.append("experiment_id")
        
        if updates:
            logger.info(f"   📝 {metric.model_name} (ID={metric.id}): Added {', '.join(updates)}")
            updated_count += 1
    
    if updated_count > 0:
        if not dry_run:
            db.commit()
            logger.info(f"\n✅ Updated {updated_count} records")
        else:
            logger.info(f"\n⚠️  DRY RUN - Would update {updated_count} records")
    else:
        logger.info("✅ All records have complete metadata")
    
    return updated_count


def main():
    parser = argparse.ArgumentParser(description='Clean up model_metrics table')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        if args.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        else:
            logger.info("⚠️  LIVE MODE - Changes will be applied to database")
        logger.info("=" * 60)
        
        # Step 1: Clean up duplicates
        kept, deleted = cleanup_duplicates(db, dry_run=args.dry_run)
        
        # Step 2: Add missing metadata
        updated = add_missing_metadata(db, dry_run=args.dry_run)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Models with duplicates: {kept}")
        logger.info(f"Records to delete: {deleted}")
        logger.info(f"Records needing metadata: {updated}")
        logger.info(f"{'='*60}\n")
        
        if args.dry_run:
            logger.info("✅ Dry run complete. Run without --dry-run to apply changes.")
        else:
            logger.info("✅ Database cleanup complete!")
            
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
