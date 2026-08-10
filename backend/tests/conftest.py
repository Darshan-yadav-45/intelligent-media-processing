"""
Shared pytest fixtures.
Uses a separate SQLite-free approach: tests expect a real PostgreSQL test DB
configured via DATABASE_URL (e.g. postgresql://.../media_pipeline_test),
since the app uses Postgres-specific UUID columns. Point .env at a test DB
before running, or use a docker-compose test service (see README).
"""
import io
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_image_bytes():
    img = PILImage.new("RGB", (400, 400), color=(120, 140, 160))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def registered_user_token(client):
    payload = {"name": "Test User", "email": "pytest_user@example.com", "password": "TestPass123!"}
    resp = client.post("/api/auth/register", json=payload)
    if resp.status_code == 409:
        resp = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    return resp.json()["access_token"]
