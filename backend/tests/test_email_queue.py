def test_email_queue_stats_and_process_endpoint(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "mailworker@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]

    client.post("/auth/request-password-reset", json={"email": "mailworker@example.com"})

    stats_before = client.get(
        "/internal/email-queue/stats",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert stats_before.status_code == 200
    before = stats_before.json()["by_status"]
    assert before.get("pending", 0) + before.get("retrying", 0) >= 1

    processed = client.post(
        "/internal/email-queue/process?batch_size=10",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert processed.status_code == 200
    payload = processed.json()
    assert payload["processed"] >= 1
    assert payload["sent"] >= 1


def test_internal_email_queue_requires_owner_or_admin(client, db_session):
    from app.models.membership import Membership
    from app.models.organization import Organization
    from app.models.user import User

    register = client.post(
        "/auth/register",
        json={
            "email": "memberonly@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]
    user = db_session.query(User).filter(User.email == "memberonly@example.com").first()
    org = (
        db_session.query(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == user.id)
        .first()
    )
    membership = (
        db_session.query(Membership)
        .filter(Membership.user_id == user.id, Membership.organization_id == org.id)
        .first()
    )
    membership.role = "member"
    db_session.commit()

    headers = {"Authorization": f"Bearer {access}", "X-Organization-Id": str(org.id)}
    denied_stats = client.get("/internal/email-queue/stats", headers=headers)
    denied_process = client.post("/internal/email-queue/process?batch_size=5", headers=headers)

    assert denied_stats.status_code == 403
    assert denied_process.status_code == 403
