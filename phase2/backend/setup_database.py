"""
Quick database setup script for forecast generation.

This script will:
1. Create the climate_dev database if it doesn't exist
2. Run migrations to create tables
3. Verify the setup
"""
import sys
import os
import subprocess

def check_postgres_running():
    """Check if PostgreSQL is running"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="",  # Try without password first
            database="postgres"
        )
        conn.close()
        return True, "postgres", ""
    except Exception as e:
        if "password authentication failed" in str(e):
            # PostgreSQL is running but needs password
            return True, "postgres", None
        return False, None, str(e)

def create_database(admin_user, admin_password):
    """Create the climate_dev database"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    try:
        # Connect to PostgreSQL server
        if admin_password:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user=admin_user,
                password=admin_password,
                database="postgres"
            )
        else:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user=admin_user,
                database="postgres"
            )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='climate_dev'")
        exists = cursor.fetchone()
        
        if exists:
            print("✓ Database 'climate_dev' already exists")
        else:
            # Create database
            cursor.execute("CREATE DATABASE climate_dev")
            print("✓ Created database 'climate_dev'")
        
        # Create user if needed
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='user'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            cursor.execute("CREATE USER \"user\" WITH PASSWORD 'pass'")
            print("✓ Created user 'user'")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE climate_dev TO \"user\"")
        print("✓ Granted privileges to user")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False

def run_migrations():
    """Run Alembic migrations"""
    try:
        print("\nRunning database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            print("✓ Migrations completed successfully")
            return True
        else:
            print(f"✗ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return False

def verify_setup():
    """Verify database setup"""
    try:
        from app.core.database import SessionLocal
        from app.models.climate_data import ClimateData
        
        db = SessionLocal()
        
        # Try to query (will fail if tables don't exist)
        count = db.query(ClimateData).count()
        db.close()
        
        print(f"✓ Database verified - {count} climate records found")
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    print("=" * 60)
    print("DATABASE SETUP FOR FORECAST GENERATION")
    print("=" * 60)
    
    # Step 1: Check PostgreSQL
    print("\n[1/4] Checking PostgreSQL...")
    running, admin_user, error = check_postgres_running()
    
    if not running:
        print(f"✗ PostgreSQL is not running: {error}")
        print("\nPlease start PostgreSQL:")
        print("  Windows: net start postgresql-x64-15")
        print("  Linux:   sudo systemctl start postgresql")
        print("  Mac:     brew services start postgresql")
        print("  Docker:  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pass postgres:15")
        return False
    
    print(f"✓ PostgreSQL is running")
    
    # Get admin password if needed
    admin_password = None
    if error is None:  # Needs password
        print("\nPostgreSQL requires authentication.")
        admin_password = input(f"Enter password for user '{admin_user}' (or press Enter to skip): ").strip()
        if not admin_password:
            admin_password = None
    
    # Step 2: Create database
    print("\n[2/4] Creating database...")
    if not create_database(admin_user, admin_password):
        print("\n⚠️  Could not create database automatically.")
        print("Please create it manually:")
        print("  psql -U postgres -c 'CREATE DATABASE climate_dev'")
        return False
    
    # Step 3: Run migrations
    print("\n[3/4] Setting up tables...")
    if not run_migrations():
        print("\n⚠️  Migrations failed. Try running manually:")
        print("  cd backend")
        print("  alembic upgrade head")
        return False
    
    # Step 4: Verify
    print("\n[4/4] Verifying setup...")
    if not verify_setup():
        print("\n⚠️  Verification failed but database might still work.")
    
    print("\n" + "=" * 60)
    print("✓ DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nYou can now run the forecast generation script:")
    print("  cd backend")
    print("  python scripts/generate_real_forecasts.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
