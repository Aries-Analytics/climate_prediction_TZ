#!/usr/bin/env python3
"""
Manual Pipeline Test Script

This script executes a manual test run of the automated forecasting pipeline
to validate configuration before enabling the scheduler.

Usage:
    python test_manual_pipeline.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add backend to path
# Script is in scripts/, backend is in backend/ (sibling of scripts/)
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Configure logging
    # Define log path ensuring logs directory exists
    log_dir = Path(__file__).parent.parent / "logs"
    log_file = log_dir / 'test_pipeline_run.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
logger = logging.getLogger(__name__)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print_section("*** AUTOMATED FORECAST PIPELINE - MANUAL TEST RUN ***")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EAT')}")
    print(f"Test Log: test_pipeline_run.log\n")
    
    try:
        # Step 1: Import dependencies
        print_section("[Step 1/5] Importing Dependencies")
        from app.core.database import SessionLocal, engine, Base
        from app.services.pipeline.orchestrator import PipelineOrchestrator
        from app.services.pipeline.alert_service import AlertService
        from dotenv import load_dotenv
        from sqlalchemy import create_engine as sa_create_engine
        from sqlalchemy.orm import sessionmaker
        print(">> All imports successful")
        
        # Step 2: Load environment
        print_section("[Step 2/5] Loading Environment Configuration")
        load_dotenv()
        
        # Check critical env vars
        required_vars = [
            'ALERT_SLACK_ENABLED', 
            'PILOT_LOCATION',
            'FORECAST_HORIZON_DAYS'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive data
                display_value = value if 'URL' not in var and 'WEBHOOK' not in var else f"{value[:30]}..."
                print(f">> {var}: {display_value}")
            else:
                print(f"XX {var}: NOT SET")
        
        # Step 3: Initialize services
        print_section("[Step 3/5] Initializing Database Connection")
        
        # Try PostgreSQL first, fall back to SQLite
        db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/climate_dev')
        test_engine = None
        db = None
        
        print(f"Attempting PostgreSQL connection...")
        try:
            test_engine = sa_create_engine(db_url)
            test_conn = test_engine.connect()
            test_conn.close()
            print(">> PostgreSQL connection successful!")
            
            # Use PostgreSQL
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            
        except Exception as pg_error:
            print(f"XX PostgreSQL connection failed: {str(pg_error)[:100]}")
            print("\n>> Falling back to SQLite for testing...")
            
            # Use SQLite instead
            sqlite_url = "sqlite:///test_climate_forecast.db"
            test_engine = sa_create_engine(sqlite_url)
            test_engine = sa_create_engine(sqlite_url)
            Base.metadata.create_all(bind=test_engine)
            TestSession = sessionmaker(bind=test_engine)
            db = TestSession()
            print(f">> SQLite database created: {sqlite_url}")
        
        print(">> Database ready")
        
        # Initialize alert service
        print("\nInitializing alert service...")
        slack_enabled = os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true'
        email_enabled = os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
        
        alert_service = AlertService(
            email_enabled=email_enabled,
            slack_enabled=slack_enabled
        )
        print(f">> Alert service initialized (Slack: {slack_enabled}, Email: {email_enabled})")
        
        # Step 4: Execute pipeline
        print_section("[Step 4/5] Executing AUTOMATED FORECAST PIPELINE (10-20 minutes)")
        print("Pipeline stages:")
        print("  1. Check incremental ingestion dates")
        print("  2. Fetch CHIRPS rainfall data (2-3 min)")
        print("  3. Fetch NASA POWER data (1-2 min)")
        print("  4. Fetch ERA5 reanalysis data (3-5 min)")
        print("  5. Fetch NDVI vegetation data (2-3 min)")
        print("  6. Fetch Ocean Indices (30 sec)")
        print("  7. Validate data quality (1 min)")
        print("  8. Generate forecasts (3-5 min)")
        print("  9. Store results in database (30 sec)\n")
        
        start_time = datetime.now()
        print(f"[CLOCK] Starting execution at {start_time.strftime('%H:%M:%S')}\n")
        
        orchestrator = PipelineOrchestrator(db, alert_service)
        result = orchestrator.execute_pipeline(execution_type='manual')
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Step 5: Display results
        print_section(f"[Step 5/5] Execution Results")
        
        print(f"Status: {result.status.upper()}")
        print(f"Execution ID: {result.execution_id}")
        print(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")
        print(f"\nData Ingestion:")
        print(f"  Records Fetched: {result.records_fetched}")
        print(f"  Records Stored: {result.records_stored}")
        
        if result.sources_succeeded:
            print(f"\n>> Successful Sources ({len(result.sources_succeeded)}):")
            for source in result.sources_succeeded:
                print(f"    * {source}")
        
        if result.sources_failed:
            print(f"\nXX Failed Sources ({len(result.sources_failed)}):")
            for source in result.sources_failed:
                print(f"    * {source}")
        
        print(f"\nForecasts:")
        print(f"  Generated: {result.forecasts_generated}")
        print(f"  Recommendations: {result.recommendations_created}")
        
        if result.status == 'failed':
            print(f"\n[ERROR] Error: {result.error_message}")
            if result.error_message:
                print(f"\nDetails: {result.error_message}")
                # details are also logged
        
        # Success summary
        print_section("*** TEST RUN COMPLETE ***")
        
        if result.status == 'completed':
            print("[SUCCESS] AUTOMATED FORECAST PIPELINE TEST SUCCESSFUL!")
            print("\nNext Steps:")
            print("  1. Check your Slack workspace for alert notifications")
            print("  2. Review test_pipeline_run.log for detailed execution log")
            print("  3. If satisfied, enable scheduler: ENABLE_SCHEDULER=true in .env")
            print("  4. Restart services to activate automated daily runs")
        else:
            print("[WARNING] PIPELINE COMPLETED WITH ISSUES")
            print("\nRecommendations:")
            print("  1. Review error messages above")
            print("  2. Check test_pipeline_run.log for details")
            print("  3. Verify API credentials in .env")
            print("  4. Fix issues before enabling scheduler")
        
        # Cleanup
        db.close()
        
        return 0 if result.status == 'completed' else 1
        
    except Exception as e:
        print_section("[FAILED] TEST RUN FAILED")
        print(f"Error: {str(e)}")
        logger.exception("Test run failed with exception")
        print("\nFull traceback saved to: test_pipeline_run.log")
        print("\nTroubleshooting:")
        print("  1. Check database connection (DATABASE_URL in .env)")
        print("  2. Verify all required packages installed (pip install -r requirements.txt)")
        print("  3. Ensure API credentials are valid")
        print("  4. Review test_pipeline_run.log for details")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
