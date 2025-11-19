import pytest
from datetime import date, timedelta
from app.models.trigger_event import TriggerEvent
from app.services import trigger_service

@pytest.fixture
def sample_triggers(db):
    """Create sample trigger events"""
    today = date.today()
    triggers = []
    
    for i in range(10):
        trigger = TriggerEvent(
            date=today - timedelta(days=i),
            trigger_type="flood" if i % 2 == 0 else "drought",
            confidence=0.8 + (i * 0.01),
            severity=0.6 + (i * 0.02),
            payout_amount=5000.0 + (i * 100)
        )
        triggers.append(trigger)
        db.add(trigger)
    
    db.commit()
    return triggers

def test_get_trigger_events(db, sample_triggers):
    """Test getting trigger events"""
    events = trigger_service.get_trigger_events(db)
    
    assert len(events) == 10

def test_get_trigger_events_filtered(db, sample_triggers):
    """Test getting filtered trigger events"""
    events = trigger_service.get_trigger_events(db, trigger_type="flood")
    
    assert len(events) == 5
    assert all(e.trigger_type == "flood" for e in events)

def test_get_trigger_timeline(db, sample_triggers):
    """Test getting trigger timeline"""
    timeline = trigger_service.get_trigger_timeline(db)
    
    assert len(timeline) > 0
    assert all(hasattr(event, 'date') for event in timeline)
    assert all(hasattr(event, 'count') for event in timeline)

def test_export_triggers_csv(db, sample_triggers):
    """Test exporting triggers to CSV"""
    csv_data = trigger_service.export_triggers_csv(db)
    
    assert csv_data is not None
    assert isinstance(csv_data, bytes)
    assert b"ID,Date,Trigger Type" in csv_data

def test_triggers_list_endpoint(client, auth_headers, sample_triggers):
    """Test triggers list endpoint"""
    response = client.get("/api/triggers", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

def test_triggers_timeline_endpoint(client, auth_headers, sample_triggers):
    """Test triggers timeline endpoint"""
    response = client.get("/api/triggers/timeline", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_triggers_export_endpoint(client, auth_headers, sample_triggers):
    """Test triggers export endpoint"""
    response = client.get("/api/triggers/export", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert b"ID,Date,Trigger Type" in response.content
