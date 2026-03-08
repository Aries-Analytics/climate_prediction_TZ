from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token, RefreshRequest
from app.services import auth_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = auth_service.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = auth_service.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = auth_service.create_user(db, user_data)
    return user

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", response_model=Token)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token"""
    user_id = auth_service.verify_refresh_token(body.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    access_token = auth_service.create_access_token(user.id)
    new_refresh_token = auth_service.create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user
