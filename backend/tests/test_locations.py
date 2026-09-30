def test_list_all_buildings(client):
    res = client.get("/api/locations/buildings")
    assert res.status_code == 200
    buildings = res.json()
    assert len(buildings) >= 5
    codes = [b["code"] for b in buildings]
    assert "ENG-A" in codes
    assert "SCI-MAIN" in codes

def test_get_building_rooms(client):
    res = client.get("/api/locations/buildings/1/rooms")
    assert res.status_code == 200
    rooms = res.json()
    assert len(rooms) > 0
    assert any(r["room_number"] == "LAB-1" for r in rooms)

def test_verify_valid_location(client):
    res = client.get("/api/locations/verify?building=ENG-A&room_number=LAB-1")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["building_code"] == "ENG-A"
    assert data["room_number"] == "LAB-1"

def test_verify_invalid_room(client):
    res = client.get("/api/locations/verify?building=ENG-A&room_number=NON_EXISTENT_999")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False

def test_search_locations(client):
    res = client.get("/api/locations/search?q=Library")
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
