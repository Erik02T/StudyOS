from app.core.config import get_settings


def test_healthcheck(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Request-Id")


def test_register_and_login_success(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "07:00-09:00",
        },
    )
    assert register_response.status_code == 201
    assert "access_token" in register_response.json()
    assert "refresh_token" in register_response.json()

    login_response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert "refresh_token" in login_response.json()


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "dup@example.com",
        "password": "Password123!",
        "available_hours_per_day": 2,
        "preferred_time_block": "19:00-21:00",
    }
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_login_invalid_credentials(client):
    client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    response = client.post("/auth/login", json={"email": "bob@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_and_logout_revocation_flow(client):
    login = client.post(
        "/auth/register",
        json={
            "email": "flow@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    tokens = login.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]

    logout = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {new_access}"},
        json={"revoke_all_sessions": True},
    )
    assert logout.status_code == 200

    denied = client.get("/organizations/", headers={"Authorization": f"Bearer {new_access}"})
    assert denied.status_code == 401


def test_v1_version_compatibility(client):
    response = client.post(
        "/v1/auth/register",
        json={
            "email": "v1@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_email_verification_flow(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "verify@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]

    request_token = client.post(
        "/auth/request-email-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert request_token.status_code == 200
    action_token = request_token.json().get("action_token")
    assert action_token

    verify = client.post("/auth/verify-email", json={"token": action_token})
    assert verify.status_code == 200
    assert verify.json()["message"] == "Email verified successfully"


def test_password_reset_flow(client):
    client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )

    request_reset = client.post("/auth/request-password-reset", json={"email": "reset@example.com"})
    assert request_reset.status_code == 200
    reset_token = request_reset.json().get("action_token")
    assert reset_token

    reset = client.post("/auth/reset-password", json={"token": reset_token, "new_password": "NewPass123!"})
    assert reset.status_code == 200

    old_login = client.post("/auth/login", json={"email": "reset@example.com", "password": "Password123!"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", json={"email": "reset@example.com", "password": "NewPass123!"})
    assert new_login.status_code == 200


def test_auth_requests_enqueue_email_jobs(client, db_session):
    from app.models.email_job import EmailJob

    register = client.post(
        "/auth/register",
        json={
            "email": "queuecheck@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]

    client.post("/auth/request-email-verification", headers={"Authorization": f"Bearer {access}"})
    client.post("/auth/request-password-reset", json={"email": "queuecheck@example.com"})

    jobs = db_session.query(EmailJob).all()
    assert len(jobs) >= 2


def test_action_tokens_are_not_exposed_outside_local(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SECRET_KEY", "staging-secret-key")
    monkeypatch.delenv("ACTION_TOKEN_EXPOSE_IN_RESPONSE", raising=False)
    monkeypatch.delenv("BILLING_ALLOW_MANUAL_PLAN_CHANGE", raising=False)
    get_settings.cache_clear()

    register = client.post(
        "/auth/register",
        json={
            "email": "masked@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]

    request_verification = client.post(
        "/auth/request-email-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert request_verification.status_code == 200
    assert request_verification.json()["action_token"] is None

    request_reset = client.post("/auth/request-password-reset", json={"email": "masked@example.com"})
    assert request_reset.status_code == 200
    assert request_reset.json()["action_token"] is None
