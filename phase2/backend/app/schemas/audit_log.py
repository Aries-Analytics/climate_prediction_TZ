from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
