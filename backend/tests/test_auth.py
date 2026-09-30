def test_student_login_success(client):
    res = client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["roll_number"] == "21CS001"
    assert data["user"]["role"] == "student"

def test_admin_login_success(client):
    res = client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "admin"

def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "wrongpassword"})
    assert res.status_code == 401
    assert "Invalid roll number or password" in res.json()["detail"]

def test_get_current_user_me(client, student_auth_headers):
    res = client.get("/api/auth/me", headers=student_auth_headers)
    assert res.status_code == 200
    assert res.json()["roll_number"] == "21CS001"

def test_refresh_token(client, student_auth_headers):
    res = client.post("/api/auth/refresh", headers=student_auth_headers)
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_unauthenticated_access_denied(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
