#!/usr/bin/env python3
"""
Manual Pipeline Test Script (Backend Version)
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure /app is in path (for Docker)
sys.path.append("/app")

try:
    from app.services.pipeline.scheduler import PipelineScheduler
    from app.core.database import SessionLocal
    from app.services.pipeline.orchestrator import PipelineOrchestrator
    from app.core.config import settings
except ImportError as e:
    logger.error(f"Failed to import pipeline components: {e}")
    sys.exit(1)

def run_manual_test():
    """Run a manual test of the pipeline"""
    logger.info("Starting manual pipeline test...")
    
    # Initialize components
    scheduler = PipelineScheduler(db_url=settings.DATABASE_URL)
    orchestrator = PipelineOrchestrator(SessionLocal())
    
    # 1. Test Scheduler Initialization
    logger.info("1. Testing Scheduler Initialization...")
    try:
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
    except Exception as e:
        logger.error(f"❌ Scheduler failed to start: {e}")
        return

    # 2. Test Forecasting Job (Trigger manually)
    logger.info("2. Testing Forecasting Job Execution...")
    try:
        locations = ["Morogoro", "Tabora", "Dodoma", "Mbeya", "Kilimanjaro", "Kagera"]
        
        logger.info(f"Running forecast generation for {len(locations)} locations...")
        # Orchestrator runs for all configured sources/locations by default
        result = orchestrator.execute_pipeline(execution_type='manual')
        
        if result.status == 'completed':
            logger.info(f"✅ Pipeline completed successfully: {result}")
        else:
            logger.warning(f"⚠️ Pipeline finished with status: {result.status}")
            
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
    finally:
        # Cleanup
        scheduler.stop()
        logger.info("Scheduler shutdown")

if __name__ == "__main__":
    run_manual_test()
