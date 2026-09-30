def test_escalation_lifecycle_and_progressive_policy(client, admin_auth_headers):
    # Log in a new student who has 0 offenses
    student_res = client.post("/api/auth/login", json={"roll_number": "22ME009", "password": "emergency123"})
    student_token = student_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Submit Alert 1
    alt1 = client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "101"}, headers=student_headers).json()
    alt1_id = alt1["id"]

    # 2. Admin Acknowledge
    ack_res = client.patch(f"/api/alerts/{alt1_id}/status", json={"status": "ACKNOWLEDGED", "remarks": "Officer en route"}, headers=admin_auth_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["new_status"] == "ACKNOWLEDGED"

    # 3. Admin mark 1st False Alert -> Warning
    false1 = client.patch(f"/api/alerts/{alt1_id}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank call 1"}, headers=admin_auth_headers)
    assert false1.status_code == 200
    assert false1.json()["escalation_triggered"] is True
    assert false1.json()["escalation_details"]["offense_number"] == 1
    assert false1.json()["escalation_details"]["warning_level"] == "warning"

    # 4. Submit Alert 2
    alt2 = client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "201"}, headers=student_headers).json()
    alt2_id = alt2["id"]

    # Admin mark 2nd False Alert -> Strong Warning
    false2 = client.patch(f"/api/alerts/{alt2_id}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank call 2"}, headers=admin_auth_headers)
    assert false2.status_code == 200
    assert false2.json()["escalation_details"]["offense_number"] == 2
    assert false2.json()["escalation_details"]["warning_level"] == "strong_warning"

    # 5. Submit Alert 3
    alt3 = client.post("/api/alerts/", json={"emergency_type": "Other Emergency", "building_id": 2, "room_number": "301"}, headers=student_headers).json()
    alt3_id = alt3["id"]

    # Admin mark 3rd False Alert -> Referred to Higher Authority
    false3 = client.patch(f"/api/alerts/{alt3_id}/status", json={"status": "RESOLVED_FALSE", "remarks": "Prank call 3"}, headers=admin_auth_headers)
    assert false3.status_code == 200
    assert false3.json()["escalation_details"]["offense_number"] == 3
    assert false3.json()["escalation_details"]["warning_level"] == "referred_to_higher_authority"

    # 6. Verify student escalation summary endpoint
    summary_res = client.get("/api/escalation/student/22ME009", headers=admin_auth_headers)
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert data["offense_count"] == 3
    assert data["warning_status"] == "referred_to_higher_authority"
    assert len(data["escalation_history"]) == 3
