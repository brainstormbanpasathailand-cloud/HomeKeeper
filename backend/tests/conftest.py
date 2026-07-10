"""Pytest fixtures: isolated in-memory DB and a TestClient with helpers."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models as _models  # noqa: F401  (populate metadata)
from app.core.ratelimit import limiter
from app.database import Base, get_db
from app.main import app

# Rate limiting is exercised by its own unit; disable for functional tests so a
# shared TestClient IP does not trip the auth limiter.
limiter.enabled = False


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def register(client):
    def _register(email="user@example.com", password="Password123", name="Test User"):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": name},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["access_token"]

    return _register


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_admin(db_session):
    """Promote a user (by email) to super_admin directly in the DB."""
    from app.models.enums import UserRole
    from app.models.user import User

    def _make(email: str, role: str = UserRole.super_admin.value):
        user = db_session.query(User).filter(User.email == email).first()
        user.role = role
        db_session.commit()
        return user

    return _make
