import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.data.seed_data import seed_database

# Use dedicated test SQLite database
TEST_DATABASE_URL = "sqlite:///./test_emergency.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Setup test tables
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Run seed script on test database
    import backend.data.seed_data as sd
    sd.engine = test_engine
    sd.SessionLocal = TestingSessionLocal
    sd.seed_database()
    
    yield
    
    # Teardown
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def student_auth_headers(client):
    res = client.post("/api/auth/login", json={"roll_number": "21CS001", "password": "emergency123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(client):
    res = client.post("/api/auth/login", json={"roll_number": "ADMIN01", "password": "emergency123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def hod_auth_headers(client):
    res = client.post("/api/auth/login", json={"roll_number": "HOD_CSE", "password": "emergency123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
