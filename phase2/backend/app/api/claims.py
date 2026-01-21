"""
Claims API endpoints for parametric insurance claims management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date

from app.core.database import get_db
from app.models.claim import Claim
from app.models.forecast import Forecast

router = APIRouter(prefix="/claims", tags=["claims"])

# Payout rates from MOROGORO_RICE_PILOT_SPECIFICATION.md
PAYOUT_RATES = {
    'drought': 60,
    'flood': 75,
    'crop_failure': 90,
    'deficit_rainfall': 60,
    'excessive_rainfall': 75
}

# Placeholder farmers per trigger until farmer registry exists
FARMERS_PER_TRIGGER = 100


# --- Schemas ---

class ApproveBatchRequest(BaseModel):
    trigger_ids: List[int]
    approved_by: int = 1  # Placeholder user ID


class ApproveBatchResponse(BaseModel):
    claims_created: int
    total_amount: float
    claim_ids: List[str]
    breakdown: dict


# --- Endpoints ---

@router.post("/approve-batch", response_model=ApproveBatchResponse)
def approve_payout_batch(
    request: ApproveBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a batch of triggers and create claim records.
    
    This endpoint:
    1. Fetches all specified triggers
    2. Calculates claim amounts based on payout rates
    3. Creates claim records with status='pending'
    4. Returns summary of created claims
    """
    
    # Fetch triggers
    triggers = db.query(Forecast).filter(Forecast.id.in_(request.trigger_ids)).all()
    
    if not triggers:
        raise HTTPException(status_code=404, detail="No triggers found with provided IDs")
    
    # Check for existing claims to prevent duplicates
    existing_claims = db.query(Claim).filter(Claim.trigger_id.in_(request.trigger_ids)).all()
    if existing_claims:
        existing_ids = [c.trigger_id for c in existing_claims]
        raise HTTPException(
            status_code=400,
            detail=f"Claims already exist for trigger IDs: {existing_ids}"
        )
    
    # Create claims
    claims_created = []
    breakdown = {}
    
    for trigger in triggers:
        # Normalize trigger type
        trigger_type = trigger.trigger_type.lower()
        
        # Get payout rate
        rate = PAYOUT_RATES.get(trigger_type, 60)  # Default to drought rate
        
        # Calculate claim amount
        # Formula: Farmers × Rate
        claim_amount = FARMERS_PER_TRIGGER * rate
        
        # Generate unique claim ID
        claim_count = db.query(Claim).count()
        claim_id = f"CLM-{datetime.now().year}-{str(claim_count + 1).zfill(4)}"
        
        # Create claim record
        claim = Claim(
            claim_id=claim_id,
            farmer_id=None,  # Placeholder
            trigger_id=trigger.id,
            trigger_type=trigger_type,
            trigger_date=trigger.target_date,
            claim_amount=claim_amount,
            status="pending",
            approved_by=request.approved_by,
            approval_date=datetime.utcnow()
        )
        
        db.add(claim)
        claims_created.append(claim)
        
        # Update breakdown
        if trigger_type not in breakdown:
            breakdown[trigger_type] = {"count": 0, "amount": 0}
        breakdown[trigger_type]["count"] += 1
        breakdown[trigger_type]["amount"] += claim_amount
    
    db.commit()
    
    # Prepare response
    total_amount = sum(c.claim_amount for c in claims_created)
    claim_ids = [c.claim_id for c in claims_created]
    
    return ApproveBatchResponse(
        claims_created=len(claims_created),
        total_amount=total_amount,
        claim_ids=claim_ids,
        breakdown=breakdown
    )


@router.get("/", response_model=List[dict])
def get_claims(
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all claims with optional status filter.
    """
    query = db.query(Claim)
    
    if status:
        query = query.filter(Claim.status == status)
    
    claims = query.order_by(Claim.created_at.desc()).all()
    return [claim.to_dict() for claim in claims]


@router.get("/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Get a specific claim by ID.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return claim.to_dict()
