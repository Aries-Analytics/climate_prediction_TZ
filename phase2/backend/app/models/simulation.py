"""
Simulation models for historical backtesting.

This module contains models for running parametric insurance simulations
against historical climate data to validate the system's performance.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class SimulationStatus(str, enum.Enum):
    """Status of a simulation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerType(str, enum.Enum):
    """Types of parametric insurance triggers."""
    DROUGHT = "drought"
    FLOOD = "flood"
    CROP_FAILURE = "crop_failure"
    DEFICIT_RAINFALL = "deficit_rainfall"
    EXCESSIVE_RAINFALL = "excessive_rainfall"


class SimulationRun(Base):
    """
    Represents a historical backtesting simulation run.
    
    A simulation applies trigger thresholds to historical climate data
    to calculate what payouts would have been made if the insurance
    product had been active during that period.
    """
    __tablename__ = "simulation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Simulation parameters
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location_name = Column(String(100), nullable=False)  # Denormalized for convenience
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    farmer_count = Column(Integer, nullable=False, default=1000)
    crop_type = Column(String(50), nullable=False, default="rice")
    
    # Premium and payout configuration
    annual_premium_per_farmer = Column(Float, default=15.0)  # USD
    drought_payout_rate = Column(Float, default=60.0)  # USD per farmer
    flood_payout_rate = Column(Float, default=75.0)
    crop_failure_payout_rate = Column(Float, default=90.0)
    
    # Execution status
    status = Column(String(20), default=SimulationStatus.PENDING.value)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Results summary (populated after completion)
    total_triggers = Column(Integer, default=0)
    total_claims = Column(Integer, default=0)
    total_premiums_collected = Column(Float, default=0.0)
    total_payouts = Column(Float, default=0.0)
    loss_ratio = Column(Float, nullable=True)  # Claims / Premiums
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    location = relationship("Location", foreign_keys=[location_id])
    farmers = relationship("SimulatedFarmer", back_populates="simulation", cascade="all, delete-orphan")
    triggers = relationship("SimulatedTrigger", back_populates="simulation", cascade="all, delete-orphan")
    claims = relationship("SimulatedClaim", back_populates="simulation", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location_id": self.location_id,
            "location_name": self.location_name,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "farmer_count": self.farmer_count,
            "crop_type": self.crop_type,
            "status": self.status,
            "total_triggers": self.total_triggers,
            "total_claims": self.total_claims,
            "total_premiums_collected": self.total_premiums_collected,
            "total_payouts": self.total_payouts,
            "loss_ratio": self.loss_ratio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class SimulatedFarmer(Base):
    """
    Represents a simulated farmer in the insurance portfolio.
    
    Farmers are distributed across villages in the Kilombero Basin
    with varying farm sizes based on realistic distributions.
    """
    __tablename__ = "simulated_farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    
    # Farmer details
    farmer_code = Column(String(20), nullable=False)  # e.g., "KLM-001"
    village = Column(String(100), nullable=False)
    hectares = Column(Float, nullable=False)
    
    # Enrollment details
    premium_paid = Column(Float, nullable=False)
    coverage_amount = Column(Float, nullable=False)
    
    # Relationships
    simulation = relationship("SimulationRun", back_populates="farmers")
    claims = relationship("SimulatedClaim", back_populates="farmer")
    
    def to_dict(self):
        return {
            "id": self.id,
            "farmer_code": self.farmer_code,
            "village": self.village,
            "hectares": self.hectares,
            "premium_paid": self.premium_paid,
            "coverage_amount": self.coverage_amount
        }


class SimulatedTrigger(Base):
    """
    Represents a trigger event detected during simulation.
    
    A trigger is fired when historical climate data breaches
    the defined thresholds for drought, flood, or other perils.
    """
    __tablename__ = "simulated_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    
    # Trigger details
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_date = Column(Date, nullable=False)
    
    # Climate data that caused trigger
    observed_value = Column(Float, nullable=False)  # e.g., rainfall mm
    threshold_value = Column(Float, nullable=False)
    deviation = Column(Float, nullable=False)  # observed - threshold
    
    # Severity classification
    severity = Column(String(20), nullable=False)  # mild, moderate, severe
    phenology_stage = Column(String(50), nullable=True)  # vegetative, flowering, etc.
    
    # Affected farmers
    farmers_affected = Column(Integer, default=0)
    payout_per_farmer = Column(Float, default=0.0)
    total_payout = Column(Float, default=0.0)
    
    # External validation
    external_validation = Column(Text, nullable=True)  # FEWS NET reference, news
    validated = Column(String(10), default="pending")  # pending, confirmed, disputed
    
    # Relationships
    simulation = relationship("SimulationRun", back_populates="triggers")
    
    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "month": self.month,
            "trigger_type": self.trigger_type,
            "trigger_date": self.trigger_date.isoformat() if self.trigger_date else None,
            "observed_value": self.observed_value,
            "threshold_value": self.threshold_value,
            "deviation": self.deviation,
            "severity": self.severity,
            "phenology_stage": self.phenology_stage,
            "farmers_affected": self.farmers_affected,
            "payout_per_farmer": self.payout_per_farmer,
            "total_payout": self.total_payout,
            "external_validation": self.external_validation,
            "validated": self.validated
        }


class SimulatedClaim(Base):
    """
    Represents a simulated insurance claim generated from a trigger.
    
    Each affected farmer gets a claim record when a trigger fires.
    """
    __tablename__ = "simulated_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("simulated_farmers.id"), nullable=False)
    trigger_id = Column(Integer, ForeignKey("simulated_triggers.id"), nullable=False)
    
    # Claim details
    claim_code = Column(String(30), nullable=False)  # e.g., "CLM-SIM-2021-001"
    year = Column(Integer, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    payout_amount = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("SimulationRun", back_populates="claims")
    farmer = relationship("SimulatedFarmer", back_populates="claims")
    
    def to_dict(self):
        return {
            "id": self.id,
            "claim_code": self.claim_code,
            "farmer_id": self.farmer_id,
            "year": self.year,
            "trigger_type": self.trigger_type,
            "payout_amount": self.payout_amount
        }
