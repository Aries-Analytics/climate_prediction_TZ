"""
Update User Passwords and Roles

Enforces standard credentials for admin, analyst, and manager roles.
Ensures the 'manager' role exists and replaces any legacy 'viewer' user.
Can be re-run to reset passwords to defaults or fix role misconfigurations.
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_credentials():
    logger.info("Starting credential update and role migration...")
    
    db = SessionLocal()
    
    try:
        # 1. Update Admin
        admin = db.query(User).filter(User.username == 'admin').first()
        if admin:
            admin.hashed_password = hash_password('AdminPass2025!')
            logger.info("✓ Updated 'admin' password")
        else:
            logger.warning("! User 'admin' not found - run seed_users.py instead")

        # 2. Update Analyst
        analyst = db.query(User).filter(User.username == 'analyst').first()
        if analyst:
            analyst.hashed_password = hash_password('AnalystPass2025!')
            logger.info("✓ Updated 'analyst' password")

        # 3. Handle Viewer -> Manager Migration
        viewer = db.query(User).filter(User.username == 'viewer').first()
        manager = db.query(User).filter(User.username == 'manager').first()

        if viewer:
            # Option A: Rename viewer to manager if manager doesn't exist
            if not manager:
                viewer.username = 'manager'
                viewer.email = 'manager@climate-insurance.tz'
                viewer.role = 'manager'
                viewer.hashed_password = hash_password('ManagerPass2025!')
                viewer.is_active = True
                logger.info("✓ Migrated 'viewer' user to 'manager' role")
            else:
                # Option B: Deactivate viewer if manager already exists
                viewer.is_active = False
                logger.info("✓ Deactivated 'viewer' user (manager already exists)")
        
        # 4. Create Manager if it didn't exist and wasn't migrated
        if not manager and not viewer:
            new_manager = User(
                username='manager',
                email='manager@climate-insurance.tz',
                role='manager',
                hashed_password=hash_password('ManagerPass2025!'),
                is_active=True
            )
            db.add(new_manager)
            logger.info("✓ Created new 'manager' user")
        elif manager:
             # Just update password if manager already existed
            manager.hashed_password = hash_password('ManagerPass2025!')
            logger.info("✓ Updated 'manager' password")

        db.commit()
        logger.info("\nSUCCESS: Credentials and roles updated.")
        
    except Exception as e:
        logger.error(f"Error updating credentials: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_credentials()
