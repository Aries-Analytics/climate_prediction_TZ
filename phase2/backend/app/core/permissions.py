from functools import wraps
from fastapi import HTTPException, status
from app.models.user import User

# Role hierarchy: admin > analyst > viewer
ROLE_HIERARCHY = {
    "admin": 3,
    "analyst": 2,
    "viewer": 1
}

# Permission definitions
PERMISSIONS = {
    "admin": [
        "read:all",
        "write:all",
        "delete:all",
        "manage:users",
        "manage:system"
    ],
    "analyst": [
        "read:all",
        "write:data",
        "write:models",
        "write:triggers"
    ],
    "viewer": [
        "read:all"
    ]
}

def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission"""
    user_permissions = PERMISSIONS.get(user.role, [])
    return permission in user_permissions

def require_role(required_role: str):
    """Decorator to require a specific role or higher"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_level = ROLE_HIERARCHY.get(current_user.role, 0)
            required_level = ROLE_HIERARCHY.get(required_role, 999)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to require a specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_permission}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator
