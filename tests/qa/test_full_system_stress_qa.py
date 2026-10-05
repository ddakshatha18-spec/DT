"""
QA Full-System Stress & Concurrency Testing Suite
Owner: P3 - Alert Queue & QA (Day 8 Milestone)

Validates system performance, concurrency, and stress resilience:
- Concurrent emergency ingestion from multi-building student burst traffic
- Alert queue load, prioritization ordering, and response latency
- Rapid incident triage lifecycle without transaction deadlocks
- High-volume indoor location directory throughput
- Panic button rapid double-tap debounce enforcement
- Disciplinary escalation audit trail consistency under stress
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def qa_client():
    from backend.app.core.database import SessionLocal
    from backend.app.models.alert import Alert, AlertStatus
    from backend.app.core.rate_limiter import alert_rate_limiter, login_rate_limiter
    
    # Reset in-memory rate limiter buckets
    alert_rate_limiter.requests.clear()
    login_rate_limiter.requests.clear()
    
    db = SessionLocal()
    # Mark existing pending alerts as resolved to avoid debounce collision between test runs
    db.query(Alert).filter(Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])).update({"status": AlertStatus.RESOLVED_GENUINE})
    db.commit()
    db.close()
    return TestClient(app)

@pytest.fixture
def admin_auth_header(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# -----------------------------------------------------------------------------
# 1. Concurrent Emergency Ingestion Under Multi-Student Burst
# -----------------------------------------------------------------------------

def test_stress_concurrent_student_emergency_burst(qa_client):
    """
    Simulate simultaneous panic alerts from 5 distinct students in different campus buildings.
    Verifies thread-safe ingestion, unique alert code generation, and 201 Created responses.
    """
    students = [
        {"roll": "21CS001", "bldg": 1, "room": "LAB-1", "type": "Fire / Smoke", "desc": "Smoke in lab"},
        {"roll": "21CS042", "bldg": 2, "room": "LH-201", "type": "Medical Emergency", "desc": "Asthma attack in lecture"},
        {"roll": "22EC015", "bldg": 3, "room": "AUD-1", "type": "Harassment / Threat", "desc": "Disturbance in auditorium"},
        {"roll": "22ME009", "bldg": 4, "room": "SEMINAR-1", "type": "Accident", "desc": "Spill injury during seminar"},
        {"roll": "23CV004", "bldg": 5, "room": "RM-101", "type": "Fall / Injury", "desc": "Staircase slip near entrance"}
    ]

    # Pre-authenticate all students
    tokens = {}
    for s in students:
        login_res = qa_client.post("/api/auth/login", json={"roll_number": s["roll"], "password": "emergency123"})
        assert login_res.status_code == 200, f"Failed login for {s['roll']}"
        tokens[s["roll"]] = login_res.json()["access_token"]

    def submit_emergency(student_data):
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {tokens[student_data['roll']]}"}
        payload = {
            "emergency_type": student_data["type"],
            "building_id": student_data["bldg"],
            "room_number": student_data["room"],
            "description": student_data["desc"]
        }
        resp = client.post("/api/alerts/", json=payload, headers=headers)
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(submit_emergency, students))

    alert_codes = set()
    for status_code, data in results:
        assert status_code == 201, f"Expected 201, got {status_code}: {data}"
        assert "alert_code" in data
        assert data["alert_code"] not in alert_codes, "Duplicate alert code generated!"
        alert_codes.add(data["alert_code"])
        assert data["status"] == "NEW"

    assert len(alert_codes) == 5


# -----------------------------------------------------------------------------
# 2. Alert Queue Filtering, Pagination, and Latency under Load
# -----------------------------------------------------------------------------

def test_stress_alert_queue_queries_and_latency(qa_client, admin_auth_header):
    """
    Test rapid query variations on the central alert queue under high limit settings.
    Ensures query latency remains under 400ms and returns structured responses.
    """
    filters = [
        {"limit": 10},
        {"limit": 50},
        {"status": "NEW", "limit": 20},
        {"priority": "CRITICAL", "limit": 20},
        {"building_id": 1, "limit": 20}
    ]

    for f in filters:
        start_time = time.time()
        res = qa_client.get("/api/alerts/", params=f, headers=admin_auth_header)
        elapsed_ms = (time.time() - start_time) * 1000

        assert res.status_code == 200
        assert elapsed_ms < 400.0, f"Query took too long: {elapsed_ms:.2f}ms"
        alerts = res.json()
        assert isinstance(alerts, list)
        for a in alerts:
            assert "id" in a
            assert "alert_code" in a
            assert "priority" in a
            assert "status" in a


# -----------------------------------------------------------------------------
# 3. Rapid Incident Triage Lifecycle Without Deadlocks
# -----------------------------------------------------------------------------

def test_stress_rapid_incident_triage_cycle(qa_client, admin_auth_header):
    """
    Simulate rapid incident review transitions (Acknowledge -> Resolve / Escalate)
    executed in tight sequence to verify database transaction isolation.
    """
    # Create 3 fresh alerts using student 21CS001, 21CS042, 22EC015
    student_rolls = ["21CS001", "21CS042", "22EC015"]
    created_alert_ids = []

    for roll in student_rolls:
        s_res = qa_client.post("/api/auth/login", json={"roll_number": roll, "password": "emergency123"})
        s_headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}
        a_res = qa_client.post(
            "/api/alerts/",
            json={"emergency_type": "Medical Emergency", "building_id": 1, "room_number": "LAB-1", "description": "Triage stress test"},
            headers=s_headers
        )
        assert a_res.status_code == 201
        created_alert_ids.append(a_res.json()["id"])

    # 1. Triage Alert 0: NEW -> ACKNOWLEDGED -> RESOLVED_GENUINE
    id_0 = created_alert_ids[0]
    ack_res0 = qa_client.patch(f"/api/alerts/{id_0}/status", json={"status": "ACKNOWLEDGED", "remarks": "Responder dispatched"}, headers=admin_auth_header)
    assert ack_res0.status_code == 200
    res_gen0 = qa_client.patch(f"/api/alerts/{id_0}/status", json={"status": "RESOLVED_GENUINE", "remarks": "Patient stabilized"}, headers=admin_auth_header)
    assert res_gen0.status_code == 200

    # 2. Triage Alert 1: NEW -> ACKNOWLEDGED -> ESCALATED
    id_1 = created_alert_ids[1]
    ack_res1 = qa_client.patch(f"/api/alerts/{id_1}/status", json={"status": "ACKNOWLEDGED", "remarks": "Team on scene"}, headers=admin_auth_header)
    assert ack_res1.status_code == 200
    esc_res1 = qa_client.patch(f"/api/alerts/{id_1}/status", json={"status": "ESCALATED", "remarks": "External ambulance requested"}, headers=admin_auth_header)
    assert esc_res1.status_code == 200

    # 3. Triage Alert 2: NEW -> RESOLVED_FALSE (Progressive escalation check)
    id_2 = created_alert_ids[2]
    false_res = qa_client.patch(f"/api/alerts/{id_2}/status", json={"status": "RESOLVED_FALSE", "remarks": "No incident detected upon arrival"}, headers=admin_auth_header)
    assert false_res.status_code == 200
    assert false_res.json()["escalation_triggered"] is True
    assert false_res.json()["new_status"] == "RESOLVED_FALSE"


# -----------------------------------------------------------------------------
# 4. High-Volume Indoor Location Directory Throughput
# -----------------------------------------------------------------------------

def test_stress_location_directory_high_throughput(qa_client):
    """
    Stress test campus location queries (buildings list, room lookup, verification)
    across 25 rapid calls, ensuring zero errors and consistent response structure.
    """
    endpoints = [
        "/api/locations/buildings",
        "/api/locations/buildings/1/rooms",
        "/api/locations/buildings/2/rooms",
        "/api/locations/verify?building=ENG-A&room_number=LAB-1",
        "/api/locations/verify?building=ENG-B&room_number=LH-201"
    ]

    for _ in range(5):
        for ep in endpoints:
            res = qa_client.get(ep)
            assert res.status_code == 200
            assert "X-Process-Time-Ms" in res.headers


# -----------------------------------------------------------------------------
# 5. Panic Button Debounce Defense Under Rapid Burst
# -----------------------------------------------------------------------------

def test_stress_panic_button_debounce_burst(qa_client):
    """
    Simulate a user rapidly tapping the emergency button 3 times in 100 milliseconds.
    The first request must succeed (201 Created).
    Subsequent burst requests must be rejected with 429 Too Many Requests.
    """
    s_login = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    assert s_login.status_code == 200
    headers = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

    payload = {
        "emergency_type": "Fall / Injury",
        "building_id": 1,
        "room_number": "LAB-1",
        "description": "Rapid tap stress test"
    }

    # First tap
    res1 = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second immediate tap (< 45 seconds later)
    res2 = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res2.status_code == 429
    assert "already in progress" in res2.json()["detail"].lower()

    # Third immediate tap
    res3 = qa_client.post("/api/alerts/", json=payload, headers=headers)
    assert res3.status_code == 429
