"""
QA Integration Workflows Test Suite
Owner: P3 - Alert Queue & QA (Day 5 Milestone)

Tests multi-service integrations:
- Location dataset mapping into alert creation
- Queue status lifecycle tracking
- SSE event broadcaster queue integration
- Multi-user concurrent emergency submission
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from shared.utils.location_dataset import CampusLocationDataset

@pytest.fixture
def qa_client():
    from backend.app.core.database import SessionLocal
    from backend.app.models.alert import Alert, AlertStatus
    db = SessionLocal()
    # Mark existing pending alerts as resolved so tests never collide on 45s debounce
    db.query(Alert).filter(Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])).update({"status": AlertStatus.RESOLVED_GENUINE})
    db.commit()
    db.close()
    return TestClient(app)

@pytest.fixture
def admin_token(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_integration_dataset_to_alert_creation(qa_client):
    """Verify that rooms loaded from P3 dataset successfully produce valid alerts."""
    # Lookup room from dataset
    room_info = CampusLocationDataset.get_room_details("ENG-A", "LAB-1")
    assert room_info is not None

    # Authenticate student
    s_res = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

    # Submit alert using dataset details
    payload = {
        "emergency_type": "Medical Emergency",
        "building_id": 1,
        "room_number": room_info["room_number"],
        "floor": room_info["floor_number"],
        "description": f"Integration Test in {room_info['room_type']}"
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res.status_code == 201
    alert = res.json()
    assert alert["priority"] == "CRITICAL"
    assert alert["building_code"] == "ENG-A"
    assert alert["room_number"] == "LAB-1"

def test_integration_alert_queue_lifecycle_and_history(qa_client, admin_token):
    """Verify complete audit history trail across multiple status transitions."""
    s_res = qa_client.post("/api/auth/login", json={"roll_number": "21CS042", "password": "emergency123"})
    headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

    # Create alert
    create_res = qa_client.post(
        "/api/alerts/",
        json={"emergency_type": "Accident", "building_id": 2, "room_number": "101"},
        headers=headers
    )
    alert_id = create_res.json()["id"]

    # Transition 1: NEW -> ACKNOWLEDGED
    qa_client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"status": "ACKNOWLEDGED", "remarks": "Paramedics arriving"},
        headers=admin_token
    )

    # Transition 2: ACKNOWLEDGED -> RESOLVED_GENUINE
    qa_client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"status": "RESOLVED_GENUINE", "remarks": "Student escorted to health center"},
        headers=admin_token
    )

    # Fetch alert detail to inspect status_history array
    detail_res = qa_client.get(f"/api/alerts/{alert_id}", headers=admin_token)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "RESOLVED_GENUINE"
    history = detail["status_history"]
    assert len(history) >= 3
    statuses = [h["new_status"] for h in history]
    assert "NEW" in statuses
    assert "ACKNOWLEDGED" in statuses
    assert "RESOLVED_GENUINE" in statuses

def test_integration_multi_user_concurrent_emergencies(qa_client, admin_token):
    """Simulate multi-user emergencies across distinct campus blocks."""
    students = [
        {"roll": "22EC015", "building": 3, "room": "101", "hazard": "Fire / Smoke", "priority": "CRITICAL"},
        {"roll": "22ME009", "building": 2, "room": "201", "hazard": "Accident", "priority": "HIGH"},
        {"roll": "23CV004", "building": 4, "room": "G-READING", "hazard": "Fall / Injury", "priority": "MEDIUM"}
    ]

    created_codes = []
    for s in students:
        s_login = qa_client.post("/api/auth/login", json={"roll_number": s["roll"], "password": "emergency123"})
        h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}
        res = qa_client.post(
            "/api/alerts/",
            json={"emergency_type": s["hazard"], "building_id": s["building"], "room_number": s["room"]},
            headers=h
        )
        assert res.status_code == 201
        created_codes.append(res.json()["alert_code"])

    # Query admin queue
    queue_res = qa_client.get("/api/alerts/?limit=20", headers=admin_token)
    assert queue_res.status_code == 200
    queue = queue_res.json()
    all_codes = [a["alert_code"] for a in queue]
    for c in created_codes:
        assert c in all_codes

def test_integration_notification_service_broadcast():
    """Verify in-memory NotificationService broadcast dispatch without crashing."""
    async def _async_test():
        from backend.app.services.notification_service import NotificationService
        
        q = NotificationService.subscribe()
        test_payload = {"alert_code": "ALT-TEST-9999", "status": "NEW"}
        await NotificationService.broadcast_alert("NEW_ALERT", test_payload)
        
        # Receive event
        event_str = await asyncio.wait_for(q.get(), timeout=2.0)
        assert "ALT-TEST-9999" in event_str
        assert "NEW_ALERT" in event_str
        NotificationService.unsubscribe(q)

    asyncio.run(_async_test())
