from datetime import date

from app.models.review import Review
from app.models.task import Task


def test_subject_crud(client, auth_header_factory):
    headers = auth_header_factory(email="subject@example.com")

    created = client.post(
        "/subjects/",
        headers=headers,
        json={"name": "Python", "importance_level": 5, "difficulty": 3, "category": "programming"},
    )
    assert created.status_code == 200
    subject_id = created.json()["id"]

    listed = client.get("/subjects/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        f"/subjects/{subject_id}",
        headers=headers,
        json={"name": "Python Avancado", "importance_level": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Python Avancado"

    deleted = client.delete(f"/subjects/{subject_id}", headers=headers)
    assert deleted.status_code == 204

    final_list = client.get("/subjects/", headers=headers)
    assert final_list.status_code == 200
    assert final_list.json() == []


def test_task_creation_initializes_review(client, db_session, auth_header_factory):
    headers = auth_header_factory(email="task@example.com")
    subject = client.post(
        "/subjects/",
        headers=headers,
        json={"name": "SQL", "importance_level": 4, "difficulty": 2, "category": "database"},
    ).json()

    task_response = client.post(
        "/tasks/",
        headers=headers,
        json={
            "subject_id": subject["id"],
            "title": "Indices",
            "estimated_time": 40,
            "mastery_level": 10,
            "status": "pending",
        },
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    review = db_session.query(Review).filter(Review.task_id == task_id).first()
    assert review is not None
    assert review.interval == 0
    assert review.ease_factor == 2.5


def test_reviews_due_and_answer_flow(client, db_session, auth_header_factory):
    headers = auth_header_factory(email="review@example.com")
    subject = client.post(
        "/subjects/",
        headers=headers,
        json={"name": "Ingles", "importance_level": 4, "difficulty": 3, "category": "language"},
    ).json()
    task = client.post(
        "/tasks/",
        headers=headers,
        json={
            "subject_id": subject["id"],
            "title": "Phrasal Verbs",
            "estimated_time": 25,
            "mastery_level": 20,
            "status": "pending",
        },
    ).json()

    review = db_session.query(Review).filter(Review.task_id == task["id"]).first()
    review.next_review_date = date.today()
    db_session.commit()

    due = client.get("/reviews/due", headers=headers)
    assert due.status_code == 200
    items = due.json()
    assert len(items) == 1
    assert items[0]["task_id"] == task["id"]
    assert items[0]["estimated_time"] == 25

    answer = client.post(
        "/reviews/answer",
        headers=headers,
        json={"task_id": task["id"], "quality": 4},
    )
    assert answer.status_code == 200
    payload = answer.json()
    assert payload["new_interval"] >= 1
    assert payload["new_mastery_level"] > payload["previous_mastery_level"]

    updated_task = db_session.query(Task).filter(Task.id == task["id"]).first()
    assert updated_task is not None
    assert updated_task.status in {"in_progress", "done"}
