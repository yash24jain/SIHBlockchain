"""
Basic auth flow test. Requires a running Postgres instance matching
DATABASE_URL (see .env / docker-compose.yml). Run with: pytest -v
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login():
    payload = {
        "username": "test_investigator",
        "email": "test_investigator@example.com",
        "password": "StrongPass123!",
    }
    reg = client.post("/auth/register", json=payload)
    assert reg.status_code in (201, 400)  # 400 if already exists from a prior run

    login = client.post(
        "/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()
