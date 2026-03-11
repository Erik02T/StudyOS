import pytest

from app.core.security import get_password_hash, verify_password


@pytest.mark.real_password_hashing
def test_password_hash_roundtrip_runtime():
    password = "Password123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert hashed.startswith("$2")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


@pytest.mark.real_password_hashing
def test_auth_flow_with_real_password_hashing(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "runtime-auth@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    assert register.status_code == 201
    register_refresh = register.json()["refresh_token"]

    login = client.post(
        "/auth/login",
        json={"email": "runtime-auth@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    login_refresh = login.json()["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": login_refresh})
    assert refreshed.status_code == 200
    refreshed_access = refreshed.json()["access_token"]
    refreshed_refresh = refreshed.json()["refresh_token"]
    assert refreshed_refresh
    assert refreshed_refresh != login_refresh

    logout = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_access}"},
        json={"revoke_all_sessions": True},
    )
    assert logout.status_code == 200

    register_refresh_denied = client.post("/auth/refresh", json={"refresh_token": register_refresh})
    assert register_refresh_denied.status_code == 401

    refreshed_refresh_denied = client.post("/auth/refresh", json={"refresh_token": refreshed_refresh})
    assert refreshed_refresh_denied.status_code == 401

    access_denied = client.get("/organizations/", headers={"Authorization": f"Bearer {refreshed_access}"})
    assert access_denied.status_code == 401
