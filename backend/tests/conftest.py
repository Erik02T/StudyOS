import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACTION_TOKEN_EXPOSE_IN_RESPONSE", "true")
os.environ.setdefault("BILLING_ALLOW_MANUAL_PLAN_CHANGE", "true")
os.environ.setdefault("EMAIL_PROVIDER", "console")
os.environ.setdefault("SENTRY_DSN", "")

from app.core import security
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.routers import auth as auth_router


@pytest.fixture(scope="session")
def test_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def testing_session_local(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session(test_engine, testing_session_local) -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def patch_password_hashing(monkeypatch, request):
    if request.node.get_closest_marker("real_password_hashing"):
        return

    def _fake_hash(password: str) -> str:
        return f"hashed::{password}"

    def _fake_verify(plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed::{plain_password}"

    monkeypatch.setattr(security, "get_password_hash", _fake_hash)
    monkeypatch.setattr(security, "verify_password", _fake_verify)
    monkeypatch.setattr(auth_router, "get_password_hash", _fake_hash)
    monkeypatch.setattr(auth_router, "verify_password", _fake_verify)


@pytest.fixture(autouse=True)
def override_test_settings(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ACTION_TOKEN_EXPOSE_IN_RESPONSE", "true")
    monkeypatch.setenv("BILLING_ALLOW_MANUAL_PLAN_CHANGE", "true")
    monkeypatch.setenv("EMAIL_PROVIDER", "console")
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("STRIPE_ALLOW_INSECURE_WEBHOOKS", raising=False)
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.fixture()
def auth_header_factory(client: TestClient):
    def _create(email: str = "user@example.com", password: str = "Password123!") -> dict:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "available_hours_per_day": 3,
                "preferred_time_block": "19:00-21:00",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _create
