import sys
import os

# Add backend to sys.path
# Go up one level from scripts folder to reach phase2, then into backend
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, 'backend'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.services import auth_service
from app.schemas.user import UserCreate

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users.")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}")
        
        if not users:
            print("No users found. Creating default admin user...")
            create_admin_user(db)
            
    except Exception as e:
        print(f"Error checking users: {e}")
    finally:
        db.close()

def create_admin_user(db: Session):
    try:
        user_data = UserCreate(
            username="admin",
            email="admin@example.com",
            password="password123",
            role="admin"
        )
        user = auth_service.create_user(db, user_data)
        print(f"Created user: {user.username} with password: password123")
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    check_users()
