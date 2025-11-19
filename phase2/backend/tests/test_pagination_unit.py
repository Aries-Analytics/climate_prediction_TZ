"""
Unit tests for pagination functionality.

**Feature: interactive-dashboard-system, Property 10: Pagination correctness**
**Validates: Requirements 4.1**

Property: For any paginated API endpoint with page P and size S, 
the response should contain exactly S items (or fewer on the last page) 
starting at offset P×S

These tests verify pagination correctness through comprehensive unit tests
covering various scenarios.
"""
import pytest
from datetime import date, timedelta
from app.models.trigger_event import TriggerEvent


def create_test_triggers(db, count: int):
    """Helper to create test trigger events"""
    # Clear existing events first to ensure clean state
    try:
        db.query(TriggerEvent).delete()
        db.commit()
    except Exception:
        db.rollback()
    
    base_date = date(2024, 1, 1)
    
    for i in range(count):
        event = TriggerEvent(
            date=base_date + timedelta(days=i),
            trigger_type="drought" if i % 2 == 0 else "flood",
            confidence=0.8,
            severity=0.6,
            payout_amount=1000.0 + (i * 100),
            location_lat=-6.0 + (i * 0.1),
            location_lon=35.0 + (i * 0.1)
        )
        db.add(event)
    
    db.commit()


def test_pagination_first_page(client, db, auth_headers):
    """Test pagination returns correct items on first page"""
    # Create 25 test items
    create_test_triggers(db, 25)
    
    # Request first page with page size 10
    response = client.get(
        "/api/triggers?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return exactly 10 items
    assert len(items) == 10
    
    # Items should be ordered by ID (ascending)
    ids = [item["id"] for item in items]
    assert ids == sorted(ids)


def test_pagination_middle_page(client, db, auth_headers):
    """Test pagination returns correct items on middle page"""
    # Create 25 test items
    create_test_triggers(db, 25)
    
    # Get first page to know the IDs
    first_page = client.get("/api/triggers?skip=0&limit=10", headers=auth_headers).json()
    
    # Request second page (skip=10, limit=10)
    response = client.get(
        "/api/triggers?skip=10&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return exactly 10 items
    assert len(items) == 10
    
    # IDs should continue from first page (no overlap)
    first_page_ids = {item["id"] for item in first_page}
    second_page_ids = {item["id"] for item in items}
    assert len(first_page_ids & second_page_ids) == 0  # No overlap


def test_pagination_last_page_partial(client, db, auth_headers):
    """Test pagination returns correct number of items on partial last page"""
    # Create 25 test items
    create_test_triggers(db, 25)
    
    # Request third page (skip=20, limit=10)
    response = client.get(
        "/api/triggers?skip=20&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return only 5 items (25 - 20 = 5 remaining)
    assert len(items) == 5
    
    # Items should still be ordered by ID
    ids = [item["id"] for item in items]
    assert ids == sorted(ids)


def test_pagination_beyond_total(client, db, auth_headers):
    """Test pagination returns empty list when skip exceeds total items"""
    # Create 10 test items
    create_test_triggers(db, 10)
    
    # Request page beyond total items (skip=20, limit=10)
    response = client.get(
        "/api/triggers?skip=20&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return empty list
    assert len(items) == 0


def test_pagination_empty_database(client, db, auth_headers):
    """Test pagination with empty database returns empty list"""
    # Don't create any items
    
    response = client.get(
        "/api/triggers?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return empty list
    assert len(items) == 0


def test_pagination_single_item(client, db, auth_headers):
    """Test pagination with single item"""
    # Create 1 test item
    create_test_triggers(db, 1)
    
    response = client.get(
        "/api/triggers?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return exactly 1 item
    assert len(items) == 1


def test_pagination_exact_page_size(client, db, auth_headers):
    """Test pagination when total items equals page size"""
    # Create exactly 10 items
    create_test_triggers(db, 10)
    
    response = client.get(
        "/api/triggers?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return exactly 10 items
    assert len(items) == 10


def test_pagination_multiple_full_pages(client, db, auth_headers):
    """Test pagination with multiple full pages"""
    # Create 30 items (3 full pages of 10)
    create_test_triggers(db, 30)
    
    all_ids = set()
    
    # Test each page
    for page in range(3):
        skip = page * 10
        response = client.get(
            f"/api/triggers?skip={skip}&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        items = response.json()
        
        # Each page should have exactly 10 items
        assert len(items) == 10
        
        # Verify no duplicate IDs across pages
        page_ids = {item["id"] for item in items}
        assert len(all_ids & page_ids) == 0  # No overlap with previous pages
        all_ids.update(page_ids)


def test_pagination_small_page_size(client, db, auth_headers):
    """Test pagination with small page size"""
    # Create 10 items
    create_test_triggers(db, 10)
    
    # Request with page size 3
    response = client.get(
        "/api/triggers?skip=0&limit=3",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return exactly 3 items
    assert len(items) == 3


def test_pagination_large_page_size(client, db, auth_headers):
    """Test pagination with large page size"""
    # Create 10 items
    create_test_triggers(db, 10)
    
    # Request with page size 100 (larger than total)
    response = client.get(
        "/api/triggers?skip=0&limit=100",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return all 10 items
    assert len(items) == 10


def test_pagination_completeness(client, db, auth_headers):
    """
    Test that paginating through all pages returns all items exactly once.
    This is a key property: the union of all pages should equal the full dataset.
    """
    # Create 47 items (not evenly divisible by page size)
    total_items = 47
    page_size = 10
    create_test_triggers(db, total_items)
    
    # Collect all items by paginating
    all_items = []
    skip = 0
    
    while True:
        response = client.get(
            f"/api/triggers?skip={skip}&limit={page_size}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        items = response.json()
        if not items:
            break
        
        all_items.extend(items)
        skip += page_size
        
        # Safety check to prevent infinite loop
        if skip > total_items + page_size:
            break
    
    # Verify we got all items
    assert len(all_items) == total_items
    
    # Verify no duplicates
    item_ids = [item["id"] for item in all_items]
    assert len(item_ids) == len(set(item_ids))
    
    # Verify items are in ascending ID order
    assert item_ids == sorted(item_ids)


def test_pagination_with_filters(client, db, auth_headers):
    """Test that pagination works correctly with filters"""
    # Clear existing events first
    try:
        db.query(TriggerEvent).delete()
        db.commit()
    except Exception:
        db.rollback()
    
    # Create 20 drought events and 20 flood events
    base_date = date(2024, 1, 1)
    
    for i in range(40):
        event = TriggerEvent(
            date=base_date + timedelta(days=i),
            trigger_type="drought" if i < 20 else "flood",
            confidence=0.8,
            severity=0.6,
            payout_amount=1000.0 + (i * 100),
            location_lat=-6.0,
            location_lon=35.0
        )
        db.add(event)
    db.commit()
    
    # Request first page of drought events only
    response = client.get(
        "/api/triggers?trigger_type=drought&skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return 10 drought events
    assert len(items) == 10
    assert all(item["trigger_type"] == "drought" for item in items)
    
    # Request second page of drought events
    response = client.get(
        "/api/triggers?trigger_type=drought&skip=10&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    items = response.json()
    
    # Should return remaining 10 drought events
    assert len(items) == 10
    assert all(item["trigger_type"] == "drought" for item in items)
