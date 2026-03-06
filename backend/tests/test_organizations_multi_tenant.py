def test_list_and_create_organizations(client, auth_header_factory):
    headers = auth_header_factory(email="orgs@example.com")

    listed = client.get("/organizations/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["role"] == "owner"

    created = client.post("/organizations/", headers=headers, json={"name": "Equipe Pro"})
    assert created.status_code == 200
    assert created.json()["slug"].startswith("equipe-pro")

    listed_again = client.get("/organizations/", headers=headers)
    assert listed_again.status_code == 200
    assert len(listed_again.json()) == 2


def test_subject_isolation_by_organization_header(client, auth_header_factory):
    headers = auth_header_factory(email="tenant@example.com")
    organizations = client.get("/organizations/", headers=headers).json()
    default_org = organizations[0]

    second_org = client.post("/organizations/", headers=headers, json={"name": "Segunda Org"}).json()

    create_default = client.post(
        "/subjects/",
        headers={**headers, "X-Organization-Id": str(default_org["id"])},
        json={"name": "Subject Default", "importance_level": 5, "difficulty": 3, "category": "general"},
    )
    assert create_default.status_code == 200

    list_default = client.get("/subjects/", headers={**headers, "X-Organization-Id": str(default_org["id"])})
    assert list_default.status_code == 200
    assert len(list_default.json()) == 1

    list_second = client.get("/subjects/", headers={**headers, "X-Organization-Id": str(second_org["id"])})
    assert list_second.status_code == 200
    assert list_second.json() == []


def _register_and_get_token(client, email: str, password: str = "Password123!") -> str:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "available_hours_per_day": 3,
            "preferred_time_block": "19:00-21:00",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _first_org_id(client, token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    orgs = client.get("/organizations/", headers=headers)
    assert orgs.status_code == 200
    return orgs.json()[0]["id"]


def _member_items(payload: dict) -> list[dict]:
    return payload["items"]


def test_owner_can_invite_promote_and_remove_member(client):
    owner_token = _register_and_get_token(client, "owner-org-mgmt@example.com")
    member_token = _register_and_get_token(client, "invitee-org-mgmt@example.com")
    assert member_token

    owner_org_id = _first_org_id(client, owner_token)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    invited = client.post(
        f"/organizations/{owner_org_id}/members/invite",
        headers=owner_headers,
        json={"email": "invitee-org-mgmt@example.com", "role": "member"},
    )
    assert invited.status_code == 200
    assert invited.json()["role"] == "member"

    members = client.get(f"/organizations/{owner_org_id}/members", headers=owner_headers)
    assert members.status_code == 200
    assert members.json()["total"] == 2
    assert len(_member_items(members.json())) == 2

    invited_user_id = next(
        row["user_id"] for row in _member_items(members.json()) if row["email"] == "invitee-org-mgmt@example.com"
    )
    promoted = client.patch(
        f"/organizations/{owner_org_id}/members/{invited_user_id}/role",
        headers=owner_headers,
        json={"role": "admin"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    removed = client.delete(f"/organizations/{owner_org_id}/members/{invited_user_id}", headers=owner_headers)
    assert removed.status_code == 204

    members_after = client.get(f"/organizations/{owner_org_id}/members", headers=owner_headers)
    assert members_after.status_code == 200
    assert members_after.json()["total"] == 1
    assert len(_member_items(members_after.json())) == 1


def test_admin_can_manage_members_but_not_owner_role(client):
    owner_token = _register_and_get_token(client, "owner-admin-flow@example.com")
    admin_user_token = _register_and_get_token(client, "admin-admin-flow@example.com")
    target_token = _register_and_get_token(client, "member-admin-flow@example.com")
    assert admin_user_token
    assert target_token

    org_id = _first_org_id(client, owner_token)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    invite_admin = client.post(
        f"/organizations/{org_id}/members/invite",
        headers=owner_headers,
        json={"email": "admin-admin-flow@example.com", "role": "admin"},
    )
    assert invite_admin.status_code == 200

    admin_headers = {"Authorization": f"Bearer {admin_user_token}"}
    invited_by_admin = client.post(
        f"/organizations/{org_id}/members/invite",
        headers=admin_headers,
        json={"email": "member-admin-flow@example.com", "role": "member"},
    )
    assert invited_by_admin.status_code == 200

    member_id = invited_by_admin.json()["user_id"]
    promote_to_admin = client.patch(
        f"/organizations/{org_id}/members/{member_id}/role",
        headers=admin_headers,
        json={"role": "admin"},
    )
    assert promote_to_admin.status_code == 200
    assert promote_to_admin.json()["role"] == "admin"

    promote_to_owner = client.patch(
        f"/organizations/{org_id}/members/{member_id}/role",
        headers=admin_headers,
        json={"role": "owner"},
    )
    assert promote_to_owner.status_code == 403


def test_cannot_remove_last_owner(client):
    owner_token = _register_and_get_token(client, "last-owner@example.com")
    org_id = _first_org_id(client, owner_token)
    headers = {"Authorization": f"Bearer {owner_token}"}

    members = client.get(f"/organizations/{org_id}/members", headers=headers)
    assert members.status_code == 200
    owner_id = _member_items(members.json())[0]["user_id"]

    remove_owner = client.delete(f"/organizations/{org_id}/members/{owner_id}", headers=headers)
    assert remove_owner.status_code == 400


def test_list_members_supports_search_role_and_pagination(client):
    owner_token = _register_and_get_token(client, "owner-search@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    org_id = _first_org_id(client, owner_token)

    for idx, role in enumerate(["member", "member", "admin"], start=1):
        email = f"filter-user-{idx}@example.com"
        _register_and_get_token(client, email)
        invited = client.post(
            f"/organizations/{org_id}/members/invite",
            headers=owner_headers,
            json={"email": email, "role": role},
        )
        assert invited.status_code == 200

    page_1 = client.get(f"/organizations/{org_id}/members?page=1&page_size=2", headers=owner_headers)
    assert page_1.status_code == 200
    assert page_1.json()["total"] == 4
    assert page_1.json()["page"] == 1
    assert page_1.json()["page_size"] == 2
    assert page_1.json()["pages"] == 2
    assert len(_member_items(page_1.json())) == 2

    page_2 = client.get(f"/organizations/{org_id}/members?page=2&page_size=2", headers=owner_headers)
    assert page_2.status_code == 200
    assert len(_member_items(page_2.json())) == 2

    admins = client.get(f"/organizations/{org_id}/members?role=admin", headers=owner_headers)
    assert admins.status_code == 200
    assert admins.json()["total"] == 1
    assert _member_items(admins.json())[0]["role"] == "admin"

    searched = client.get(f"/organizations/{org_id}/members?search=filter-user-2", headers=owner_headers)
    assert searched.status_code == 200
    assert searched.json()["total"] == 1
    assert _member_items(searched.json())[0]["email"] == "filter-user-2@example.com"

    sorted_by_email = client.get(
        f"/organizations/{org_id}/members?sort_by=email&sort_dir=asc&page=1&page_size=10",
        headers=owner_headers,
    )
    assert sorted_by_email.status_code == 200
    emails = [item["email"] for item in _member_items(sorted_by_email.json())]
    assert emails == sorted(emails)

    sorted_by_role = client.get(
        f"/organizations/{org_id}/members?sort_by=role&sort_dir=desc&page=1&page_size=10",
        headers=owner_headers,
    )
    assert sorted_by_role.status_code == 200
    roles = [item["role"] for item in _member_items(sorted_by_role.json())]
    assert roles == sorted(roles, reverse=True)
