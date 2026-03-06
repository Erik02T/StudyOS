def test_sessions_finalize_idempotency_key_prevents_duplicates(client, auth_header_factory):
    headers = auth_header_factory(email="idempotency@example.com")
    headers_with_key = {**headers, "Idempotency-Key": "session-abc-123"}

    first = client.post(
        "/sessions/finalize",
        headers=headers_with_key,
        json={
            "source": "manual",
            "study_minutes": 60,
            "completed_tasks": 2,
            "focus_score": 80,
            "time_block": "19:00-21:00",
        },
    )
    assert first.status_code == 200
    first_payload = first.json()

    second = client.post(
        "/sessions/finalize",
        headers=headers_with_key,
        json={
            "source": "manual",
            "study_minutes": 60,
            "completed_tasks": 2,
            "focus_score": 80,
            "time_block": "19:00-21:00",
        },
    )
    assert second.status_code == 200
    second_payload = second.json()

    assert first_payload["performance_id"] == second_payload["performance_id"]
    assert first_payload["study_minutes"] == second_payload["study_minutes"]
    assert first_payload["completed_tasks"] == second_payload["completed_tasks"]


def test_sessions_finalize_idempotency_key_conflict_for_different_payload(client, auth_header_factory):
    headers = auth_header_factory(email="idempotency-conflict@example.com")
    headers_with_key = {**headers, "Idempotency-Key": "session-xyz-456"}

    first = client.post(
        "/sessions/finalize",
        headers=headers_with_key,
        json={
            "source": "manual",
            "study_minutes": 30,
            "completed_tasks": 1,
            "focus_score": 70,
            "time_block": "19:00-21:00",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/sessions/finalize",
        headers=headers_with_key,
        json={
            "source": "manual",
            "study_minutes": 90,
            "completed_tasks": 3,
            "focus_score": 85,
            "time_block": "19:00-21:00",
        },
    )
    assert second.status_code == 409


def test_analytics_events_visible_for_admin_scope(client, auth_header_factory):
    headers = auth_header_factory(email="events-owner@example.com")

    finalize = client.post(
        "/sessions/finalize",
        headers=headers,
        json={
            "source": "manual",
            "study_minutes": 45,
            "completed_tasks": 1,
            "focus_score": 75,
            "time_block": "18:00-20:00",
        },
    )
    assert finalize.status_code == 200

    events = client.get("/analytics/events?page=1&page_size=20", headers=headers)
    assert events.status_code == 200
    payload = events.json()
    assert payload["total"] >= 1
    assert any(item["event_type"] == "session.finalized" for item in payload["items"])
