"""
Legacy wrapper for backward compatibility.
Please use pipelines/run_data_pipeline.py instead.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from the new location
from pipelines import run_data_pipeline

# Re-export the main function for backward compatibility
def run_pipeline(debug=False, start_year=2000, end_year=2023):
    """
    Legacy function - redirects to new pipeline location.
    
    Args:
        debug: If True, runs in dry-run mode
        start_year: Start year for data ingestion
        end_year: End year for data ingestion
    """
    print("⚠️  WARNING: run_pipeline.py is deprecated.")
    print("   Please use: python pipelines/run_data_pipeline.py")
    print()
    
    # Call the new pipeline
    return run_data_pipeline.run_pipeline(debug=debug, start_year=start_year, end_year=end_year)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Legacy pipeline wrapper')
    parser.add_argument('--debug', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--start-year', type=int, default=2000, help='Start year')
    parser.add_argument('--end-year', type=int, default=2023, help='End year')
    
    args = parser.parse_args()
    
    run_pipeline(debug=args.debug, start_year=args.start_year, end_year=args.end_year)
