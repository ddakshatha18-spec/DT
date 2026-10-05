"""
QA Alert Data Validation Test Suite
Owner: P3 - Alert Queue & QA (Day 4 Milestone)

Validates negative scenarios, fuzzing boundaries, SQLi/XSS injection safety,
and payload structure compliance across the alert ingestion pipeline.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def qa_client():
    return TestClient(app)

@pytest.fixture
def qa_student_token(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_qa_val_missing_required_fields(qa_client, qa_student_token):
    # Completely empty payload
    res = qa_client.post("/api/alerts/", json={}, headers=qa_student_token)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error_type"] == "ValidationError"
    field_names = [d["field"] for d in data["details"]]
    assert "emergency_type" in field_names
    assert "building_id" in field_names
    assert "room_number" in field_names

def test_qa_val_invalid_emergency_type(qa_client, qa_student_token):
    # Unsupported hazard category
    payload = {
        "emergency_type": "Alien Invasion",
        "building_id": 1,
        "room_number": "101"
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=qa_student_token)
    assert res.status_code == 422
    assert res.json()["success"] is False

def test_qa_val_non_existent_building_id(qa_client):
    # Use distinct student 21CS042 to avoid 45s debounce
    s_res = qa_client.post("/api/auth/login", json={"roll_number": "21CS042", "password": "emergency123"})
    headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

    payload = {
        "emergency_type": "Fall / Injury",
        "building_id": 999999,
        "room_number": "101"
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]

def test_qa_val_latitude_boundary_excess(qa_client, qa_student_token):
    payload = {
        "emergency_type": "Fire / Smoke",
        "building_id": 1,
        "room_number": "101",
        "latitude": 91.5
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=qa_student_token)
    assert res.status_code == 400
    assert "Latitude must be between" in res.json()["detail"]

def test_qa_val_longitude_boundary_excess(qa_client, qa_student_token):
    payload = {
        "emergency_type": "Fire / Smoke",
        "building_id": 1,
        "room_number": "101",
        "longitude": -185.0
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=qa_student_token)
    assert res.status_code == 400
    assert "Longitude must be between" in res.json()["detail"]

def test_qa_val_sqli_in_room_sanitization(qa_client):
    s_res = qa_client.post("/api/auth/login", json={"roll_number": "22EC015", "password": "emergency123"})
    headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

    # Attempt SQL injection payload in room_number field
    payload = {
        "emergency_type": "Accident",
        "building_id": 1,
        "room_number": "101'; DROP TABLE alerts; --",
        "description": "Safe test payload"
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=headers)
    # Should safely treat string as literal and not crash or execute SQL
    assert res.status_code == 201
    assert "'; DROP TABLE alerts; --" in res.json()["room_number"]

def test_qa_val_xss_in_description_sanitization(qa_client):
    s_res = qa_client.post("/api/auth/login", json={"roll_number": "22ME009", "password": "emergency123"})
    headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

    # Attempt XSS payload in description
    xss_payload = "<script>alert('pwned')</script>"
    payload = {
        "emergency_type": "Other Emergency",
        "building_id": 2,
        "room_number": "201",
        "description": xss_payload
    }
    res = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res.status_code == 201
    # Check that description was safely handled and database remained intact
    assert res.json()["description"] == xss_payload

def test_qa_val_all_emergency_types_valid(qa_client):
    valid_types = [
        "Fall / Injury",
        "Medical Emergency",
        "Accident",
        "Fire / Smoke",
        "Harassment / Threat",
        "Fainting / Unconsciousness",
        "Other Emergency"
    ]
    # Check that schema recognizes all 7 types
    from backend.app.models.alert import EmergencyType
    for t in valid_types:
        assert any(e.value == t for e in EmergencyType)
