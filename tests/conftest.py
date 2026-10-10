"""Shared test setup.

The tests NEVER touch your real database: they use a temporary in-memory
SQLite database and the built-in mock AI provider (no API key needed).
"""
import os

# These must be set BEFORE the app is imported (settings are read at import time).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-pytest-0123456789"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402,F401
from app.database.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import UserRole  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services import user_service  # noqa: E402

PASSWORD = "Passw0rd!"


@pytest.fixture()
def session_factory():
    # StaticPool keeps ONE in-memory database alive for the whole test.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_headers(client, session_factory):
    """Create a user directly in the database, log in, and return auth headers."""

    def _make(email: str, role: UserRole = UserRole.USER):
        with session_factory() as db:
            user_service.create_user(db, UserCreate(name="Test Person", email=email, password=PASSWORD), role=role)
        response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make


@pytest.fixture()
def user_headers(make_headers):
    return make_headers("alice@example.com")


@pytest.fixture()
def other_user_headers(make_headers):
    return make_headers("bob@example.com")


@pytest.fixture()
def admin_headers(make_headers):
    return make_headers("admin@example.com", UserRole.ADMIN)
