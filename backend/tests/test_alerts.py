def test_submit_alert_fire_smoke_critical(client, student_auth_headers):
    payload = {
        "emergency_type": "Fire / Smoke",
        "building_id": 1,
        "room_number": "LAB-1",
        "description": "Thick smoke visible"
    }
    res = client.post("/api/alerts/", json=payload, headers=student_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["priority"] == "CRITICAL"
    assert data["status"] == "NEW"
    assert data["building_code"] == "ENG-A"
    assert "ALT-" in data["alert_code"]

def test_submit_alert_invalid_building(client):
    # Use distinct student 21CS042
    s_res = client.post("/api/auth/login", json={"roll_number": "21CS042", "password": "emergency123"})
    token = s_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "emergency_type": "Fall / Injury",
        "building_id": 99999,
        "room_number": "101"
    }
    res = client.post("/api/alerts/", json=payload, headers=headers)
    assert res.status_code == 404

def test_duplicate_alert_debounce_rate_limit(client, student_auth_headers):
    # Immediately sending another alert with same student 21CS001 triggers 429 debounce
    payload = {
        "emergency_type": "Medical Emergency",
        "building_id": 1,
        "room_number": "102"
    }
    res = client.post("/api/alerts/", json=payload, headers=student_auth_headers)
    assert res.status_code == 429
    assert "already in progress" in res.json()["detail"]

def test_list_alerts_student_view(client, student_auth_headers):
    res = client.get("/api/alerts/", headers=student_auth_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)

def test_list_alerts_admin_view(client, admin_auth_headers):
    res = client.get("/api/alerts/", headers=admin_auth_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
