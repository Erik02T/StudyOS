def _promote_to_member(db_session, email: str):
    from app.models.membership import Membership
    from app.models.organization import Organization
    from app.models.user import User

    user = db_session.query(User).filter(User.email == email).first()
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
    return org.id


def test_member_can_create_but_cannot_delete_subject(client, db_session):
    register = client.post(
        "/auth/register",
        json={
            "email": "rbac-subject@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]
    org_id = _promote_to_member(db_session, "rbac-subject@example.com")
    headers = {"Authorization": f"Bearer {access}", "X-Organization-Id": str(org_id)}

    created = client.post(
        "/subjects/",
        headers=headers,
        json={"name": "RBAC Subject", "importance_level": 4, "difficulty": 3, "category": "general"},
    )
    assert created.status_code == 200
    subject_id = created.json()["id"]

    denied_delete = client.delete(f"/subjects/{subject_id}", headers=headers)
    assert denied_delete.status_code == 403


def test_member_can_update_task_but_cannot_delete(client, db_session):
    register = client.post(
        "/auth/register",
        json={
            "email": "rbac-task@example.com",
            "password": "Password123!",
            "available_hours_per_day": 2,
            "preferred_time_block": "19:00-21:00",
        },
    )
    access = register.json()["access_token"]
    org_id = _promote_to_member(db_session, "rbac-task@example.com")
    headers = {"Authorization": f"Bearer {access}", "X-Organization-Id": str(org_id)}

    subject = client.post(
        "/subjects/",
        headers=headers,
        json={"name": "Task Subject", "importance_level": 4, "difficulty": 3, "category": "general"},
    ).json()
    task = client.post(
        "/tasks/",
        headers=headers,
        json={
            "subject_id": subject["id"],
            "title": "Task RBAC",
            "estimated_time": 30,
            "mastery_level": 10,
            "status": "pending",
        },
    ).json()

    updated = client.put(f"/tasks/{task['id']}", headers=headers, json={"title": "Task RBAC Updated"})
    assert updated.status_code == 200

    denied_delete = client.delete(f"/tasks/{task['id']}", headers=headers)
    assert denied_delete.status_code == 403

