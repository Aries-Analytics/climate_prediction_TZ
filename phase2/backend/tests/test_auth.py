import pytest
from app.services import auth_service
from app.schemas.user import UserCreate

def test_create_user(db):
    """Test user creation"""
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="password123",
        role="viewer"
    )
    
    user = auth_service.create_user(db, user_data)
    
    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.role == "viewer"
    assert user.is_active is True
    assert user.hashed_password != "password123"  # Password should be hashed

def test_authenticate_user_success(db, test_user):
    """Test successful authentication"""
    authenticated = auth_service.authenticate_user(db, "testuser", "testpass123")
    
    assert authenticated is not None
    assert authenticated.id == test_user.id
    assert authenticated.username == test_user.username

def test_authenticate_user_wrong_password(db, test_user):
    """Test authentication with wrong password"""
    authenticated = auth_service.authenticate_user(db, "testuser", "wrongpassword")
    
    assert authenticated is None

def test_authenticate_user_nonexistent(db):
    """Test authentication with nonexistent user"""
    authenticated = auth_service.authenticate_user(db, "nonexistent", "password")
    
    assert authenticated is None

def test_create_access_token(test_user):
    """Test JWT token creation"""
    token = auth_service.create_access_token(test_user.id)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token(test_user):
    """Test JWT token verification"""
    token = auth_service.create_access_token(test_user.id)
    user_id = auth_service.verify_token(token)
    
    assert user_id == test_user.id

def test_verify_invalid_token():
    """Test verification of invalid token"""
    user_id = auth_service.verify_token("invalid_token")
    
    assert user_id is None

def test_register_endpoint(client):
    """Test user registration endpoint"""
    response = client.post("/api/auth/register", json={
        "username": "apiuser",
        "email": "api@example.com",
        "password": "apipass123",
        "role": "analyst"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "apiuser"
    assert data["email"] == "api@example.com"
    assert "hashed_password" not in data

def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "different@example.com",
        "password": "password123",
        "role": "analyst"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_login_endpoint(client, test_user):
    """Test login endpoint"""
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_credentials(client, test_user):
    """Test login with wrong credentials"""
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401

def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/api/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_get_current_user_no_auth(client):
    """Test getting current user without authentication"""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 403  # No auth header
