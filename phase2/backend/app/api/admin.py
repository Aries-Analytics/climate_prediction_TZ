"""
Admin API endpoints for user management and audit logs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.forecast_log import ForecastLog
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.schemas.audit_log import AuditLogResponse
from app.services.auth_service import create_user, update_user, delete_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    """
    users = db.query(User).order_by(User.created_at.desc(), User.id.desc()).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_existing_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Update a user (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = update_user(db=db, user_id=user_id, user_data=user_data)
    return updated_user


@router.delete("/users/{user_id}")
async def delete_existing_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    delete_user(db=db, user_id=user_id)
    return {"message": "User deleted successfully"}


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and search (admin only).
    
    Filters:
    - user_id: Filter by user ID
    - action: Filter by action type
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Order by most recent first, with ID as secondary sort for pagination stability
    query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return logs


@router.get("/health")
async def admin_health_check(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    System health check (admin only).
    """
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        # Get some basic stats
        user_count = db.query(User).count()
        audit_log_count = db.query(AuditLog).count()
        forecast_log_count = db.query(ForecastLog).count()

        return {
            "status": "healthy",
            "database": "connected",
            "users": user_count,
            "audit_logs": audit_log_count,
            "forecast_logs": forecast_log_count,
            "shadow_run_target": 1080
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
