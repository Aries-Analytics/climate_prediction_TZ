"""
Simulation API endpoints for historical backtesting.

These endpoints allow users to create, run, and analyze historical
simulations of the parametric insurance system.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.simulation import SimulationRun, SimulatedTrigger, SimulatedClaim, SimulationStatus
from app.services.backtesting_service import BacktestingService

router = APIRouter(prefix="/simulation", tags=["simulation"])


# --- Schemas ---

class CreateSimulationRequest(BaseModel):
    """Request to create a new simulation run."""
    name: str
    description: Optional[str] = None
    location_id: int
    start_year: int = 2015
    end_year: int = 2025
    farmer_count: int = 1000
    crop_type: str = "rice"
    annual_premium_per_farmer: float = 91.0  # Sustainable premium (75% loss ratio)


class SimulationResponse(BaseModel):
    """Response containing simulation details."""
    id: int
    name: str
    description: Optional[str]
    location_name: str
    start_year: int
    end_year: int
    farmer_count: int
    crop_type: str
    status: str
    total_triggers: int
    total_claims: int
    total_premiums_collected: float
    total_payouts: float
    loss_ratio: Optional[float]
    created_at: Optional[str]
    completed_at: Optional[str]


class TriggerSummary(BaseModel):
    """Summary of a trigger event."""
    year: int
    month: int
    trigger_type: str
    severity: str
    observed_value: float
    threshold_value: float
    total_payout: float
    validated: str
    external_validation: Optional[str]


class YearlySummary(BaseModel):
    """Summary of triggers and payouts for a year."""
    year: int
    trigger_count: int
    total_payout: float
    validated: bool
    triggers: List[TriggerSummary]


# --- Endpoints ---

@router.post("/", response_model=dict)
def create_simulation(
    request: CreateSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new historical backtesting simulation.
    
    This creates the simulation record but does not run it yet.
    Use POST /simulation/{id}/run to execute the simulation.
    """
    service = BacktestingService(db)
    
    try:
        simulation = service.create_simulation(
            name=request.name,
            description=request.description,
            location_id=request.location_id,
            start_year=request.start_year,
            end_year=request.end_year,
            farmer_count=request.farmer_count,
            crop_type=request.crop_type,
            annual_premium_per_farmer=request.annual_premium_per_farmer
        )
        
        return {
            "message": "Simulation created successfully",
            "simulation_id": simulation.id,
            "status": simulation.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{simulation_id}/run")
def run_simulation(
    simulation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a backtesting simulation.
    
    This runs the full simulation:
    1. Generates farmer portfolio
    2. Fetches historical climate data
    3. Applies trigger thresholds
    4. Generates claims
    5. Calculates summary metrics
    """
    simulation = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if simulation.status == SimulationStatus.RUNNING.value:
        raise HTTPException(status_code=400, detail="Simulation is already running")
    
    if simulation.status == SimulationStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Simulation already completed. Create a new simulation to run again.")
    
    # Run synchronously for now (small datasets)
    service = BacktestingService(db)
    
    try:
        result = service.run_phase_based_simulation(simulation_id)
        return {
            "message": "Simulation completed successfully",
            "simulation_id": result.id,
            "status": result.status,
            "total_triggers": result.total_triggers,
            "total_payouts": result.total_payouts,
            "loss_ratio": result.loss_ratio
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/", response_model=List[dict])
def list_simulations(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all simulations, optionally filtered by status."""
    query = db.query(SimulationRun)
    
    if status:
        query = query.filter(SimulationRun.status == status)
    
    simulations = query.order_by(SimulationRun.created_at.desc()).all()
    return [sim.to_dict() for sim in simulations]


@router.get("/{simulation_id}")
def get_simulation(
    simulation_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed simulation results."""
    service = BacktestingService(db)
    summary = service.get_simulation_summary(simulation_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return summary


@router.get("/{simulation_id}/triggers")
def get_simulation_triggers(
    simulation_id: int,
    db: Session = Depends(get_db)
):
    """Get all trigger events from a simulation."""
    triggers = db.query(SimulatedTrigger).filter(
        SimulatedTrigger.simulation_id == simulation_id
    ).order_by(SimulatedTrigger.year, SimulatedTrigger.month).all()
    
    return [t.to_dict() for t in triggers]


@router.get("/{simulation_id}/claims")
def get_simulation_claims(
    simulation_id: int,
    year: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get claims from a simulation, optionally filtered by year."""
    query = db.query(SimulatedClaim).filter(
        SimulatedClaim.simulation_id == simulation_id
    )
    
    if year:
        query = query.filter(SimulatedClaim.year == year)
    
    claims = query.limit(limit).all()
    return [c.to_dict() for c in claims]


@router.get("/{simulation_id}/report")
def get_validation_report(
    simulation_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a validation report for the simulation.
    
    This report includes:
    - Executive summary
    - Year-by-year trigger analysis
    - External validation (FEWS NET cross-references)
    - Sustainability analysis
    - Limitations and assumptions
    """
    service = BacktestingService(db)
    summary = service.get_simulation_summary(simulation_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulation = summary["simulation"]
    yearly = summary["yearly_summary"]
    sustainability = summary["sustainability_analysis"]
    
    # Build report
    report = {
        "title": f"Historical Backtesting Validation Report: {simulation['name']}",
        "generated_at": datetime.utcnow().isoformat(),
        
        "executive_summary": {
            "location": simulation["location_name"],
            "period": f"{simulation['start_year']} - {simulation['end_year']}",
            "farmers_simulated": simulation["farmer_count"],
            "crop": simulation["crop_type"],
            "total_triggers": simulation["total_triggers"],
            "total_payouts": simulation["total_payouts"],
            "loss_ratio": simulation["loss_ratio"],
            "sustainability": sustainability["recommendation"]
        },
        
        "methodology": {
            "data_sources": ["CHIRPS Rainfall", "NASA POWER", "ERA5 Reanalysis"],
            "trigger_types": ["Drought (vegetative)", "Drought (flowering)", "Flood"],
            "thresholds": {
                "drought_vegetative": "<50mm/month",
                "drought_flowering": "<80mm/month",
                "flood": ">300mm/month"
            },
            "payout_model": "Per-farmer fixed rate",
            "premium": "$15/farmer/year"
        },
        
        "yearly_analysis": yearly,
        
        "external_validation": summary["external_validation"],
        
        "sustainability_analysis": sustainability,
        
        "limitations": [
            "Simulated farmer portfolio - not actual enrollees",
            "Ground truth yield data not available",
            "Basis risk cannot be fully quantified without farmer loss reports",
            "Premium adequacy based on historical patterns only"
        ],
        
        "assumptions": [
            "All farmers in portfolio affected equally by triggers",
            "Climate data accurately represents actual conditions",
            "Trigger thresholds are appropriately calibrated for rice",
            "Payout rates are sufficient to support farmer recovery"
        ]
    }
    
    return report


@router.delete("/{simulation_id}")
def delete_simulation(
    simulation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a simulation and all associated data."""
    simulation = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    db.delete(simulation)
    db.commit()
    
    return {"message": "Simulation deleted successfully"}
