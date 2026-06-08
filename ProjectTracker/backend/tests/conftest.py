"""
Shared fixtures for all tests.
Uses an in-memory SQLite DB so tests never touch the real database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.auth import get_password_hash

# StaticPool forces ALL sessions to reuse the same underlying connection, so
# CREATE TABLE done by reset_db is visible to every subsequent query.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db):
    user = User(
        name="Test Admin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, admin_user):
    res = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "testpass123"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": "Bearer " + token}
