"""
User Seeding Script

Creates initial admin, analyst, and viewer accounts for the dashboard.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_users():
    """
    Create initial user accounts.
    """
    logger.info("Seeding initial user accounts...")
    
    db = SessionLocal()
    
    try:
        # Default users
        users_to_create = [
            {
                'username': 'admin',
                'email': 'admin@climate-insurance.tz',
                'password': 'admin123',  # Change in production!
                'role': 'admin',
                'is_active': True
            },
            {
                'username': 'analyst',
                'email': 'analyst@climate-insurance.tz',
                'password': 'analyst123',
                'role': 'analyst',
                'is_active': True
            },
            {
                'username': 'viewer',
                'email': 'viewer@climate-insurance.tz',
                'password': 'viewer123',
                'role': 'viewer',
                'is_active': True
            }
        ]
        
        created_users = []
        
        for user_data in users_to_create:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == user_data['username']).first()
            
            if existing_user:
                logger.info(f"  - User '{user_data['username']}' already exists, skipping")
                continue
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                hashed_password=hash_password(user_data['password']),
                role=user_data['role'],
                is_active=user_data['is_active']
            )
            
            db.add(user)
            created_users.append(user_data)
            logger.info(f"  ✓ Created user: {user_data['username']} ({user_data['role']})")
        
        db.commit()
        
        if created_users:
            logger.info(f"\n✓ Successfully created {len(created_users)} users")
            logger.info("\n" + "=" * 60)
            logger.info("INITIAL CREDENTIALS (Change passwords after first login!)")
            logger.info("=" * 60)
            for user in created_users:
                logger.info(f"\n{user['role'].upper()}:")
                logger.info(f"  Username: {user['username']}")
                logger.info(f"  Password: {user['password']}")
                logger.info(f"  Email: {user['email']}")
            logger.info("\n" + "=" * 60)
        else:
            logger.info("\nNo new users created (all users already exist)")
        
        # Verification
        total_users = db.query(User).count()
        logger.info(f"\nTotal users in database: {total_users}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = seed_users()
    sys.exit(0 if success else 1)
