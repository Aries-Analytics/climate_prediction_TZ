"""
API endpoints for Location management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.location import Location
from app.core.auth import get_current_user


router = APIRouter(prefix="/locations", tags=["locations"])


class LocationResponse(BaseModel):
    """Response schema for location data."""
    id: int
    name: str
    latitude: float
    longitude: float
    region: str | None
    population: int | None
    climate_zone: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=List[LocationResponse])
def get_locations(
    db: Session = Depends(get_db)
):
    """
    Get all monitored locations.
    
    Returns list of all geographic locations being monitored for triggers.
    Useful for mapping coordinates to location names and filtering by region.
    """
    locations = db.query(Location).order_by(Location.name).all()
    return locations


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific location by ID.
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location
