import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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
def patch_password_hashing(monkeypatch):
    def _fake_hash(password: str) -> str:
        return f"hashed::{password}"

    def _fake_verify(plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed::{plain_password}"

    monkeypatch.setattr(security, "get_password_hash", _fake_hash)
    monkeypatch.setattr(security, "verify_password", _fake_verify)
    monkeypatch.setattr(auth_router, "get_password_hash", _fake_hash)
    monkeypatch.setattr(auth_router, "verify_password", _fake_verify)


@pytest.fixture(autouse=True)
def override_test_settings():
    os.environ["ACTION_TOKEN_EXPOSE_IN_RESPONSE"] = "true"
    os.environ["EMAIL_PROVIDER"] = "console"
    os.environ["SENTRY_DSN"] = ""
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
