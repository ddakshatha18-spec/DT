"""
QA End-to-End Scenario Testing Suite
Owner: P3 - Alert Queue & QA (Day 6 Milestone)

Tests complete user journeys matching the design thinking abstract:
- Critical fire scenario with immediate triage
- Panic button debounce defense
- Full false alarm progressive escalation cycle
- Department HOD monitoring workflow
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def qa_client():
    from backend.app.core.database import SessionLocal
    from backend.app.models.alert import Alert, AlertStatus
    db = SessionLocal()
    # Mark existing pending alerts as resolved so tests do not collide on 45s debounce
    db.query(Alert).filter(Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])).update({"status": AlertStatus.RESOLVED_GENUINE})
    db.commit()
    db.close()
    return TestClient(app)

def test_e2e_journey_critical_fire_emergency(qa_client):
    """Journey 1: Student reports fire -> Admin acknowledges -> Resolves genuine."""
    # 1. Student logs in
    s_login = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    assert s_login.status_code == 200
    s_token = s_login.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # 2. Student verifies room
    loc_res = qa_client.get("/api/locations/verify?building=ENG-A&room_number=LAB-1")
    assert loc_res.status_code == 200
    assert loc_res.json()["valid"] is True

    # 3. Student triggers alert
    alert_res = qa_client.post(
        "/api/alerts/",
        json={"emergency_type": "Fire / Smoke", "building_id": 1, "room_number": "LAB-1", "description": "Server rack on fire"},
        headers=s_headers
    )
    assert alert_res.status_code == 201
    alert_id = alert_res.json()["id"]
    assert alert_res.json()["priority"] == "CRITICAL"

    # 4. Security Admin logs in and checks queue
    a_login = qa_client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    a_token = a_login.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    queue = qa_client.get("/api/alerts/?status=NEW", headers=a_headers).json()
    assert any(a["id"] == alert_id for a in queue)

    # 5. Admin acknowledges
    ack = qa_client.patch(f"/api/alerts/{alert_id}/status", json={"status": "ACKNOWLEDGED", "remarks": "Fire team dispatched"}, headers=a_headers)
    assert ack.status_code == 200

    # 6. Admin resolves genuine
    resolve = qa_client.patch(f"/api/alerts/{alert_id}/status", json={"status": "RESOLVED_GENUINE", "remarks": "Extinguished"}, headers=a_headers)
    assert resolve.status_code == 200
    assert resolve.json()["new_status"] == "RESOLVED_GENUINE"

def test_e2e_journey_panic_button_double_tap_debounce(qa_client):
    """Journey 2: Stressed student double taps panic button within seconds."""
    s_login = qa_client.post("/api/auth/login", json={"roll_number": "21CS042", "password": "emergency123"})
    s_headers = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

    # First tap
    res1 = qa_client.post(
        "/api/alerts/",
        json={"emergency_type": "Medical Emergency", "building_id": 3, "room_number": "G02"},
        headers=s_headers
    )
    assert res1.status_code == 201

    # Second tap immediately after
    res2 = qa_client.post(
        "/api/alerts/",
        json={"emergency_type": "Medical Emergency", "building_id": 3, "room_number": "G02"},
        headers=s_headers
    )
    assert res2.status_code == 429
    assert "already in progress" in res2.json()["detail"]

def test_e2e_journey_false_alarm_escalation_cycle(qa_client):
    """Journey 3: Student triggers 3 false alarms, escalating to formal referral."""
    from backend.app.core.database import SessionLocal
    from backend.app.models.user import User, WarningLevel
    db = SessionLocal()
    st = db.query(User).filter(User.roll_number == "22ME009").first()
    if st:
        st.offense_count = 0
        st.warning_status = WarningLevel.NONE
        db.commit()
    db.close()

    s_login = qa_client.post("/api/auth/login", json={"roll_number": "22ME009", "password": "emergency123"})
    s_headers = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

    a_login = qa_client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    a_headers = {"Authorization": f"Bearer {a_login.json()['access_token']}"}

    # False alarm 1
    a1 = qa_client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "101"}, headers=s_headers).json()
    f1 = qa_client.patch(f"/api/alerts/{a1['id']}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank 1"}, headers=a_headers).json()
    assert f1["escalation_details"]["warning_level"] == "warning"

    # False alarm 2
    a2 = qa_client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "201"}, headers=s_headers).json()
    f2 = qa_client.patch(f"/api/alerts/{a2['id']}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank 2"}, headers=a_headers).json()
    assert f2["escalation_details"]["warning_level"] == "strong_warning"

    # False alarm 3
    a3 = qa_client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "301"}, headers=s_headers).json()
    f3 = qa_client.patch(f"/api/alerts/{a3['id']}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank 3"}, headers=a_headers).json()
    assert f3["escalation_details"]["warning_level"] == "referred_to_higher_authority"

    # Verify disciplinary summary
    student_summary = qa_client.get("/api/escalation/student/22ME009", headers=a_headers).json()
    assert student_summary["offense_count"] == 3
    assert student_summary["warning_status"] == "referred_to_higher_authority"

def test_e2e_journey_hod_department_monitoring(qa_client):
    """Journey 4: Department HOD logs in and reviews student escalation and reports."""
    hod_login = qa_client.post("/api/auth/login", json={"roll_number": "HOD_CSE", "password": "emergency123"})
    assert hod_login.status_code == 200
    hod_headers = {"Authorization": f"Bearer {hod_login.json()['access_token']}"}

    # HOD queries all registered students in department
    students = qa_client.get("/api/auth/users/students", headers=hod_headers)
    assert students.status_code == 200
    assert len(students.json()) > 0

    # HOD views full escalation logs
    logs = qa_client.get("/api/escalation/logs", headers=hod_headers)
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)
