import pytest
from datetime import date, timedelta
from app.models.trigger_event import TriggerEvent
from app.services import dashboard_service

@pytest.fixture
def sample_triggers(db):
    """Create sample trigger events"""
    today = date.today()
    triggers = [
        TriggerEvent(
            date=today - timedelta(days=i),
            trigger_type="flood",
            confidence=0.8,
            severity=0.6,
            payout_amount=5000.0
        ) for i in range(5)
    ] + [
        TriggerEvent(
            date=today - timedelta(days=i),
            trigger_type="drought",
            confidence=0.9,
            severity=0.7,
            payout_amount=7000.0
        ) for i in range(3)
    ]
    
    for trigger in triggers:
        db.add(trigger)
    db.commit()
    
    return triggers

def test_calculate_trigger_rate(db, sample_triggers):
    """Test trigger rate calculation"""
    today = date.today()
    start_date = today - timedelta(days=30)
    
    rate = dashboard_service.calculate_trigger_rate(db, "flood", start_date, today)
    
    assert rate.trigger_type == "flood"
    assert rate.count == 5
    assert rate.rate > 0

def test_get_executive_kpis(db, sample_triggers):
    """Test executive KPIs retrieval"""
    kpis = dashboard_service.get_executive_kpis(db)
    
    assert kpis is not None
    assert kpis.flood_trigger_rate is not None
    assert kpis.drought_trigger_rate is not None
    assert kpis.crop_failure_trigger_rate is not None
    assert kpis.total_triggers_ytd > 0
    assert kpis.estimated_payouts_ytd > 0

def test_get_loss_ratio_trend(db, sample_triggers):
    """Test loss ratio trend calculation"""
    trend = dashboard_service.get_loss_ratio_trend(db, months=12)
    
    assert trend is not None
    assert trend.target_threshold == 0.70
    assert isinstance(trend.data, list)

def test_get_sustainability_status(db, sample_triggers):
    """Test sustainability status"""
    status = dashboard_service.get_sustainability_status(db)
    
    assert status is not None
    assert status.status in ["sustainable", "warning", "unsustainable"]
    assert status.loss_ratio >= 0
    assert status.threshold == 0.70

def test_dashboard_executive_endpoint(client, auth_headers, sample_triggers):
    """Test executive dashboard endpoint"""
    response = client.get("/api/dashboard/executive", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "flood_trigger_rate" in data
    assert "drought_trigger_rate" in data
    assert "loss_ratio" in data
    assert "sustainability_status" in data

def test_dashboard_requires_auth(client):
    """Test that dashboard endpoints require authentication"""
    response = client.get("/api/dashboard/executive")
    
    assert response.status_code == 403
