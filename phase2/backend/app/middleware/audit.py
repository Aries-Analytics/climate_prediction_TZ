"""
Audit logging middleware for tracking user actions and data access.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal
import json


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log authentication events, data access, and configuration changes.
    """
    
    # Actions that should be audited
    AUDIT_ACTIONS = {
        'POST /api/auth/login': 'user_login',
        'POST /api/auth/register': 'user_register',
        'POST /api/auth/logout': 'user_logout',
        'GET /api/dashboard/executive': 'view_executive_dashboard',
        'GET /api/models': 'view_models',
        'GET /api/triggers': 'view_triggers',
        'GET /api/climate': 'view_climate_data',
        'GET /api/risk': 'view_risk_data',
        'POST /api/risk/scenario': 'run_scenario_analysis',
        'GET /api/triggers/export': 'export_trigger_data',
        'PUT /api/admin/users': 'update_user',
        'DELETE /api/admin/users': 'delete_user',
        'POST /api/admin/users': 'create_user',
    }
    
    async def dispatch(self, request: Request, call_next):
        # Get request details
        method = request.method
        path = request.url.path
        action_key = f"{method} {path}"
        
        # Check if this action should be audited
        action = None
        for pattern, action_name in self.AUDIT_ACTIONS.items():
            if path.startswith(pattern.split()[1]):
                action = action_name
                break
        
        # Process the request
        response = await call_next(request)
        
        # Log audit entry if action should be audited and request was successful
        if action and 200 <= response.status_code < 300:
            try:
                # Get user ID from request state (set by auth dependency)
                user_id = getattr(request.state, 'user_id', None)
                
                # Get client IP
                client_ip = request.client.host if request.client else None
                
                # Create audit log entry
                db = SessionLocal()
                try:
                    audit_log = AuditLog(
                        user_id=user_id,
                        action=action,
                        resource=path,
                        details={'method': method, 'status_code': response.status_code},
                        ip_address=client_ip
                    )
                    db.add(audit_log)
                    db.commit()
                finally:
                    db.close()
            except Exception as e:
                # Don't fail the request if audit logging fails
                print(f"Audit logging error: {e}")
        
        return response


def log_authentication_event(db: Session, user_id: int, action: str, ip_address: str = None, success: bool = True):
    """
    Log authentication events (login, logout, failed attempts).
    """
    try:
        audit_log = AuditLog(
            user_id=user_id if success else None,
            action=action,
            resource='authentication',
            details={'success': success},
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log authentication event: {e}")
        db.rollback()


def log_data_access(db: Session, user_id: int, resource: str, action: str, details: dict = None):
    """
    Log data access events.
    """
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {}
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log data access: {e}")
        db.rollback()


def log_configuration_change(db: Session, user_id: int, resource: str, before: dict, after: dict):
    """
    Log configuration changes with before/after values.
    """
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action='configuration_change',
            resource=resource,
            details={
                'before': before,
                'after': after
            }
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log configuration change: {e}")
        db.rollback()
