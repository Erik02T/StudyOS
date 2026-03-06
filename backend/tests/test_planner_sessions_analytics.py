from datetime import date

from app.models.review import Review


def _create_subject(client, headers, name="Matematica", category="math"):
    response = client.post(
        "/subjects/",
        headers=headers,
        json={"name": name, "importance_level": 5, "difficulty": 3, "category": category},
    )
    return response.json()


def _create_task(client, headers, subject_id, title, estimated_time=30, mastery_level=20, status="pending"):
    response = client.post(
        "/tasks/",
        headers=headers,
        json={
            "subject_id": subject_id,
            "title": title,
            "estimated_time": estimated_time,
            "mastery_level": mastery_level,
            "status": status,
        },
    )
    return response.json()


def test_generate_plan_with_context(client, db_session, auth_header_factory):
    headers = auth_header_factory(email="planner@example.com")
    subject = _create_subject(client, headers, name="Fisica", category="science")
    task_a = _create_task(client, headers, subject["id"], "Cinematica", estimated_time=40, mastery_level=10)
    _create_task(client, headers, subject["id"], "Dinamica", estimated_time=35, mastery_level=30)

    review = db_session.query(Review).filter(Review.task_id == task_a["id"]).first()
    review.next_review_date = date.today()
    db_session.commit()

    response = client.post(
        "/planner/generate-plan",
        headers=headers,
        json={"available_minutes": 120, "time_block": "06:00-08:00"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["available_minutes"] == 120
    assert payload["time_block"] == "06:00-08:00"
    assert "scheduled_reviews" in payload
    assert "scheduled_new_tasks" in payload
    assert "planning_context" in payload


def test_finalize_session_and_analytics_dashboard(client, auth_header_factory):
    headers = auth_header_factory(email="analytics@example.com")
    subject = _create_subject(client, headers, name="Historia", category="humanities")
    _create_task(client, headers, subject["id"], "Brasil Colonial", status="done", mastery_level=90)
    _create_task(client, headers, subject["id"], "Republica Velha", status="pending", mastery_level=40)

    first = client.post(
        "/sessions/finalize",
        headers=headers,
        json={
            "source": "manual",
            "study_minutes": 50,
            "completed_tasks": 1,
            "focus_score": 80,
            "time_block": "19:00-21:00",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/sessions/finalize",
        headers=headers,
        json={
            "source": "review",
            "study_minutes": 25,
            "quality": 4,
            "time_block": "07:00-09:00",
        },
    )
    assert second.status_code == 200
    assert second.json()["study_minutes"] >= 75

    summary = client.get("/analytics/summary?days=30", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["entries"] >= 1
    assert summary.json()["avg_study_minutes"] > 0

    heatmap = client.get("/analytics/heatmap?days=30", headers=headers)
    assert heatmap.status_code == 200
    assert "best_time_bucket" in heatmap.json()
    assert len(heatmap.json()["heatmap"]) == 5

    dashboard = client.get("/analytics/dashboard?days=30", headers=headers)
    assert dashboard.status_code == 200
    dash_payload = dashboard.json()
    assert "progress" in dash_payload
    assert "evolution_score" in dash_payload["progress"]
    assert "consistency" in dash_payload


def test_analytics_performance_accumulate_mode(client, auth_header_factory):
    headers = auth_header_factory(email="accumulate@example.com")

    first = client.post(
        "/analytics/performance",
        headers=headers,
        json={
            "accumulate": True,
            "completed_tasks": 1,
            "study_minutes": 30,
            "focus_score": 70,
            "time_block": "19:00-21:00",
        },
    )
    assert first.status_code == 200
    assert first.json()["study_minutes"] == 30

    second = client.post(
        "/analytics/performance",
        headers=headers,
        json={
            "accumulate": True,
            "completed_tasks": 2,
            "study_minutes": 40,
            "focus_score": 90,
            "time_block": "19:00-21:00",
        },
    )
    assert second.status_code == 200
    assert second.json()["study_minutes"] == 70
    assert second.json()["completed_tasks"] == 3

