"""
Initialize database with migrations and create a test user.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, SessionLocal
from app.models import Base
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate

def init_database():
    """Initialize database tables and create test user"""
    print("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create test user
    db = SessionLocal()
    try:
        auth_service = AuthService()
        
        # Check if user already exists
        from app.models.user import User
        existing_user = db.query(User).filter(User.username == "admin").first()
        
        if existing_user:
            print("✓ Admin user already exists")
        else:
            # Create admin user
            user_data = UserCreate(
                username="admin",
                email="admin@example.com",
                password="admin123",
                full_name="Admin User"
            )
            
            user = auth_service.create_user(db, user_data)
            print(f"✓ Created admin user: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Password: admin123")
        
        print("\n✓ Database initialization complete!")
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
