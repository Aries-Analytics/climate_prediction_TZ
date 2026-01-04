"""
Geographic API endpoints for location data and mapping.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.location import Location
from app.models.trigger_event import TriggerEvent
from app.core.dependencies import get_current_active_user as get_current_user

router = APIRouter(prefix="/api", tags=["geography"])


@router.get("/locations")
async def get_locations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all monitored locations.
    
    Returns list of locations with coordinates and metadata.
    """
    locations = db.query(Location).all()
    return [loc.to_dict() for loc in locations]


@router.get("/locations/{location_id}")
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get details for a specific location.
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location.to_dict()


@router.get("/locations/{location_id}/triggers")
async def get_location_triggers(
    location_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    trigger_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get trigger events for a specific location.
    
    Filters:
    - start_date: Start date for trigger events
    - end_date: End date for trigger events
    - trigger_type: Filter by type (drought, flood, crop_failure)
    """
    # Get location
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Query triggers for this location
    query = db.query(TriggerEvent).filter(
        TriggerEvent.location_lat == location.latitude,
        TriggerEvent.location_lon == location.longitude
    )
    
    # Apply filters
    if start_date:
        query = query.filter(TriggerEvent.date >= start_date)
    if end_date:
        query = query.filter(TriggerEvent.date <= end_date)
    if trigger_type:
        query = query.filter(TriggerEvent.trigger_type == trigger_type)
    
    triggers = query.order_by(TriggerEvent.date.desc()).all()
    
    return {
        "location": location.to_dict(),
        "trigger_count": len(triggers),
        "triggers": [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "trigger_type": t.trigger_type,
                "confidence": t.confidence,
                "severity": t.severity,
                "payout_amount": t.payout_amount
            }
            for t in triggers
        ]
    }


@router.get("/locations/summary")
async def get_locations_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get trigger summary for all locations.
    
    Returns aggregated trigger counts and payouts by location.
    """
    locations = db.query(Location).all()
    
    summary = []
    for location in locations:
        # Query triggers for this location
        query = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == location.latitude,
            TriggerEvent.location_lon == location.longitude
        )
        
        if start_date:
            query = query.filter(TriggerEvent.date >= start_date)
        if end_date:
            query = query.filter(TriggerEvent.date <= end_date)
        
        triggers = query.all()
        
        # Count by type
        drought_count = sum(1 for t in triggers if t.trigger_type == 'drought')
        flood_count = sum(1 for t in triggers if t.trigger_type == 'flood')
        crop_count = sum(1 for t in triggers if t.trigger_type == 'crop_failure')
        
        total_payout = sum(t.payout_amount or 0 for t in triggers)
        
        summary.append({
            "location": location.to_dict(),
            "triggers": {
                "drought": drought_count,
                "flood": flood_count,
                "crop_failure": crop_count,
                "total": len(triggers)
            },
            "total_payout": total_payout,
            "active_triggers": drought_count + flood_count + crop_count
        })
    
    return summary


@router.get("/triggers/geojson")
async def get_triggers_geojson(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    trigger_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Export trigger events as GeoJSON for mapping.
    
    Returns GeoJSON FeatureCollection with trigger events as point features.
    """
    query = db.query(TriggerEvent)
    
    # Apply filters
    if start_date:
        query = query.filter(TriggerEvent.date >= start_date)
    if end_date:
        query = query.filter(TriggerEvent.date <= end_date)
    if trigger_type:
        query = query.filter(TriggerEvent.trigger_type == trigger_type)
    
    triggers = query.all()
    
    features = []
    for trigger in triggers:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [trigger.location_lon, trigger.location_lat]
            },
            "properties": {
                "id": trigger.id,
                "date": trigger.date.isoformat(),
                "trigger_type": trigger.trigger_type,
                "confidence": trigger.confidence,
                "severity": trigger.severity,
                "payout_amount": trigger.payout_amount
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "count": len(features),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "trigger_type": trigger_type
        }
    }
