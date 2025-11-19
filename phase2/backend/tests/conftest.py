import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import User, ClimateData, TriggerEvent, ModelMetric, ModelPrediction, AuditLog
from app.services import auth_service

# Disable audit middleware for tests to avoid PostgreSQL connection attempts
# The audit middleware tries to connect to the production database which slows down tests
app.user_middleware.clear()  # Remove all middleware including audit middleware

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user"""
    from app.schemas.user import UserCreate
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        role="analyst"
    )
    user = auth_service.create_user(db, user_data)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user"""
    token = auth_service.create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    from app.schemas.user import UserCreate
    user_data = UserCreate(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        role="admin"
    )
    user = auth_service.create_user(db, user_data)
    return user

@pytest.fixture
def admin_headers(admin_user):
    """Get authentication headers for admin user"""
    token = auth_service.create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}


# Property-based testing fixtures
@pytest.fixture(scope="function")
def pbt_db_client():
    """
    Create a database and client for property-based tests.
    This fixture returns a tuple (db, client) that can be used within
    Hypothesis test examples without fixture scope issues.
    """
    # Create fresh database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Setup client with database override
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    yield (db, client)
    
    # Cleanup
    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)
