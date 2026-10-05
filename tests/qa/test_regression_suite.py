"""
QA Regression Test Suite
Owner: P3 - Alert Queue & QA (Day 7 Milestone)

Comprehensive regression testing verifying:
- Authentication boundaries, invalid credentials, missing/tampered Bearer tokens
- Session token refresh and profile resolution
- Strict Role-Based Access Control (RBAC) boundaries (Student vs HOD vs Admin)
- Terminal status immutability (closed alerts cannot be reopened or re-transitioned)
- Student alert queue data isolation (no cross-student data leakage)
- Indoor location verification boundary conditions
- HTTP security headers compliance (nosniff, frame denial, XSS protection, timing)
- OpenAPI and interactive documentation endpoint availability
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

@pytest.fixture
def student_auth_header(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def hod_auth_header(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "HOD_CSE", "password": "emergency123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def admin_auth_header(qa_client):
    res = qa_client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# -----------------------------------------------------------------------------
# 1. Authentication Boundaries & Session Security
# -----------------------------------------------------------------------------

def test_regression_auth_invalid_credentials(qa_client):
    """Verify system blocks non-existent users and mismatched passwords with 401."""
    # Invalid password
    res1 = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "wrong_password"})
    assert res1.status_code == 401
    assert "detail" in res1.json()

    # Non-existent user
    res2 = qa_client.post("/api/auth/login", json={"roll_number": "NON_EXISTENT_999", "password": "emergency123"})
    assert res2.status_code == 401


def test_regression_auth_missing_or_corrupted_bearer_token(qa_client):
    """Protected endpoints must reject missing, empty, or corrupted Bearer headers."""
    protected_endpoints = [
        ("GET", "/api/auth/me"),
        ("GET", "/api/alerts/"),
        ("GET", "/api/escalation/logs"),
        ("POST", "/api/auth/refresh")
    ]
    for method, endpoint in protected_endpoints:
        # No header
        res_no_auth = qa_client.request(method, endpoint)
        assert res_no_auth.status_code == 401, f"{endpoint} should reject missing auth"

        # Corrupted token
        res_bad_auth = qa_client.request(method, endpoint, headers={"Authorization": "Bearer bad.token.here"})
        assert res_bad_auth.status_code == 401, f"{endpoint} should reject malformed token"


def test_regression_session_refresh_lifecycle(qa_client, student_auth_header):
    """Verify session refresh produces a valid functional token."""
    refresh_res = qa_client.post("/api/auth/refresh", headers=student_auth_header)
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    new_token = new_data["access_token"]
    assert new_token != ""

    # Verify new token works on /me
    me_res = qa_client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["roll_number"] == "21CS001"


# -----------------------------------------------------------------------------
# 2. Strict Role-Based Access Control (RBAC) Boundaries
# -----------------------------------------------------------------------------

def test_regression_student_forbidden_from_admin_operations(qa_client, student_auth_header):
    """Students must receive 403 Forbidden for elevated administrative endpoints."""
    # Attempting to fetch audit escalation logs
    logs_res = qa_client.get("/api/escalation/logs", headers=student_auth_header)
    assert logs_res.status_code == 403

    # Attempting to view disciplinary summary
    summary_res = qa_client.get("/api/escalation/student/21CS001", headers=student_auth_header)
    assert summary_res.status_code == 403

    # Attempting to list all students
    users_res = qa_client.get("/api/auth/users/students", headers=student_auth_header)
    assert users_res.status_code == 403

    # Attempting to review/patch alert status
    patch_res = qa_client.patch(
        "/api/alerts/1/status",
        json={"status": "ACKNOWLEDGED", "remarks": "Unauthorized triage attempt"},
        headers=student_auth_header
    )
    assert patch_res.status_code == 403


def test_regression_hod_role_access(qa_client, hod_auth_header):
    """HOD role must have read and review access to escalation logs and alert stats."""
    logs_res = qa_client.get("/api/escalation/logs", headers=hod_auth_header)
    assert logs_res.status_code == 200
    assert isinstance(logs_res.json(), list)

    users_res = qa_client.get("/api/auth/users/students", headers=hod_auth_header)
    assert users_res.status_code == 200
    assert isinstance(users_res.json(), list)


# -----------------------------------------------------------------------------
# 3. Terminal Status Immutability
# -----------------------------------------------------------------------------

def test_regression_alert_terminal_state_immutability(qa_client, student_auth_header, admin_auth_header):
    """Once an emergency incident is finalized (RESOLVED), it cannot be re-opened."""
    # 1. Create alert
    create_res = qa_client.post(
        "/api/alerts/",
        json={
            "emergency_type": "Medical Emergency",
            "building_id": 1,
            "room_number": "LAB-1",
            "description": "Regression test incident immutability"
        },
        headers=student_auth_header
    )
    assert create_res.status_code == 201
    alert_id = create_res.json()["id"]

    # 2. Finalize alert as RESOLVED_GENUINE
    resolve_res = qa_client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"status": "RESOLVED_GENUINE", "remarks": "Medical assistance provided successfully"},
        headers=admin_auth_header
    )
    assert resolve_res.status_code == 200

    # 3. Attempt to illegally mutate closed alert back to ACKNOWLEDGED
    reopen_res = qa_client.patch(
        f"/api/alerts/{alert_id}/status",
        json={"status": "ACKNOWLEDGED", "remarks": "Attempting to reopen closed incident"},
        headers=admin_auth_header
    )
    assert reopen_res.status_code == 400
    assert "already finalized" in reopen_res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 4. Student Queue Data Isolation
# -----------------------------------------------------------------------------

def test_regression_student_queue_isolation(qa_client, admin_auth_header):
    """Students must only see their own submitted alerts; Admins see all campus alerts."""
    # Login Student 1
    s1_login = qa_client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    s1_headers = {"Authorization": f"Bearer {s1_login.json()['access_token']}"}

    # Login Student 2
    s2_login = qa_client.post("/api/auth/login", json={"roll_number": "22EC015", "password": "emergency123"})
    s2_headers = {"Authorization": f"Bearer {s2_login.json()['access_token']}"}

    # Student 1 submits alert
    create_res = qa_client.post(
        "/api/alerts/",
        json={
            "emergency_type": "Harassment / Threat",
            "building_id": 2,
            "room_number": "LH-201",
            "description": "Student 1 isolation check"
        },
        headers=s1_headers
    )
    assert create_res.status_code == 201
    s1_alert_id = create_res.json()["id"]

    # Student 2 requests their queue: s1_alert_id must NOT be present
    s2_queue = qa_client.get("/api/alerts/", headers=s2_headers).json()
    assert all(a["id"] != s1_alert_id for a in s2_queue)

    # Admin requests queue: s1_alert_id MUST be present
    admin_queue = qa_client.get("/api/alerts/", headers=admin_auth_header).json()
    assert any(a["id"] == s1_alert_id for a in admin_queue)


# -----------------------------------------------------------------------------
# 5. Indoor Location Verification Boundaries
# -----------------------------------------------------------------------------

def test_regression_location_verification_boundaries(qa_client):
    """Test boundary checks for valid/invalid building codes and room numbers."""
    # Valid room and building
    res_valid = qa_client.get("/api/locations/verify?building=ENG-A&room_number=LAB-1")
    assert res_valid.status_code == 200
    assert res_valid.json()["valid"] is True

    # Invalid room in valid building
    res_inv_room = qa_client.get("/api/locations/verify?building=ENG-A&room_number=NON_EXISTENT_999")
    assert res_inv_room.status_code == 200
    assert res_inv_room.json()["valid"] is False

    # Invalid building code
    res_inv_bldg = qa_client.get("/api/locations/verify?building=UNKNOWN_XYZ&room_number=LAB-1")
    assert res_inv_bldg.status_code == 200
    assert res_inv_bldg.json()["valid"] is False


# -----------------------------------------------------------------------------
# 6. HTTP Security Headers and Processing Timing
# -----------------------------------------------------------------------------

def test_regression_http_security_headers_compliance(qa_client):
    """Every HTTP response must deliver hardened security headers and latency telemetry."""
    res = qa_client.get("/api/locations/buildings")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Process-Time-Ms" in res.headers
    process_time = float(res.headers.get("X-Process-Time-Ms"))
    assert process_time >= 0.0


# -----------------------------------------------------------------------------
# 7. Documentation and Schema Integrity
# -----------------------------------------------------------------------------

def test_regression_api_documentation_endpoints(qa_client):
    """Interactive Swagger, ReDoc, and OpenAPI schema endpoints must be active."""
    docs_res = qa_client.get("/docs")
    assert docs_res.status_code == 200

    redoc_res = qa_client.get("/redoc")
    assert redoc_res.status_code == 200

    openapi_res = qa_client.get("/api/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    assert "openapi" in schema
    assert "/api/alerts/" in schema["paths"]
    assert "/api/auth/login" in schema["paths"]
