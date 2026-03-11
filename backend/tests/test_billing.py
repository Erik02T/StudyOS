from app.core.config import get_settings


def _register(client, email: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_subscription_defaults_and_manual_upgrade(client):
    headers = _register(client, "billing-owner@example.com")

    current = client.get("/billing/subscription", headers=headers)
    assert current.status_code == 200
    assert current.json()["plan"] == "free"
    assert len(current.json()["usage"]) == 3

    updated = client.patch("/billing/subscription", headers=headers, json={"plan": "pro"})
    assert updated.status_code == 200
    assert updated.json()["plan"] == "pro"


def test_free_plan_subject_limit_enforced(client):
    headers = _register(client, "billing-limit@example.com")
    for idx in range(10):
        response = client.post(
            "/subjects/",
            headers=headers,
            json={
                "name": f"Subject {idx}",
                "importance_level": 3,
                "difficulty": 3,
                "category": "general",
            },
        )
        assert response.status_code == 200

    denied = client.post(
        "/subjects/",
        headers=headers,
        json={
            "name": "Overflow Subject",
            "importance_level": 3,
            "difficulty": 3,
            "category": "general",
        },
    )
    assert denied.status_code == 402


def test_member_cannot_manage_billing(client):
    owner_headers = _register(client, "owner-billing-rbac@example.com")
    _register(client, "member-billing-rbac@example.com")

    orgs = client.get("/organizations/", headers=owner_headers).json()
    org_id = orgs[0]["id"]

    invite = client.post(
        f"/organizations/{org_id}/members/invite",
        headers=owner_headers,
        json={"email": "member-billing-rbac@example.com", "role": "member"},
    )
    assert invite.status_code == 200

    login_member = client.post(
        "/auth/login",
        json={"email": "member-billing-rbac@example.com", "password": "Password123!"},
    )
    assert login_member.status_code == 200
    member_headers = {
        "Authorization": f"Bearer {login_member.json()['access_token']}",
        "X-Organization-Id": str(org_id),
    }

    view_denied = client.get("/billing/subscription", headers=member_headers)
    assert view_denied.status_code == 403
    manage_denied = client.patch("/billing/subscription", headers=member_headers, json={"plan": "pro"})
    assert manage_denied.status_code == 403


def test_checkout_session_requires_stripe_configuration(client):
    headers = _register(client, "billing-checkout@example.com")
    response = client.post(
        "/billing/checkout-session",
        headers=headers,
        json={
            "plan": "pro",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        },
    )
    assert response.status_code == 503


def test_stripe_webhook_requires_explicit_secure_configuration(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SECRET_KEY", "staging-secret-key")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.delenv("ACTION_TOKEN_EXPOSE_IN_RESPONSE", raising=False)
    monkeypatch.delenv("BILLING_ALLOW_MANUAL_PLAN_CHANGE", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("STRIPE_ALLOW_INSECURE_WEBHOOKS", raising=False)
    get_settings.cache_clear()

    response = client.post("/billing/webhook/stripe", json={"type": "ping"})

    assert response.status_code == 503
    assert "STRIPE_WEBHOOK_SECRET" in response.json()["detail"]
