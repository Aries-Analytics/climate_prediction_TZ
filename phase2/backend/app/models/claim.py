"""
Claim model for parametric insurance claims.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Claim(Base):
    """Model for insurance claims triggered by climate events."""
    
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), unique=True, nullable=False, index=True)  # CLM-2026-0001
    farmer_id = Column(Integer, nullable=True)  # Placeholder until farmer registry exists
    trigger_id = Column(Integer, ForeignKey("forecasts.id"), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_date = Column(DateTime, nullable=False)
    claim_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, processing, disbursed, failed
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    disbursement_date = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trigger = relationship("Forecast", foreign_keys=[trigger_id])
    
    def __repr__(self):
        return f"<Claim(claim_id='{self.claim_id}', amount={self.claim_amount}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "farmer_id": self.farmer_id,
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type,
            "trigger_date": self.trigger_date.isoformat() if self.trigger_date else None,
            "claim_amount": self.claim_amount,
            "status": self.status,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "disbursement_date": self.disbursement_date.isoformat() if self.disbursement_date else None,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
