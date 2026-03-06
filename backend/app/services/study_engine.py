from datetime import date, timedelta
from math import ceil
from statistics import mean

from sqlalchemy.orm import Session

from app.models.performance import Performance
from app.models.review import Review
from app.models.subject import Subject
from app.models.task import Task
from app.models.user import User
from app.services.pareto_engine import ParetoEngine


class StudyEngine:
    @staticmethod
    def _extract_start_hour(time_block: str) -> int:
        try:
            raw_hour = time_block.split("-")[0].split(":")[0]
            hour = int(raw_hour)
            if 0 <= hour <= 23:
                return hour
        except (ValueError, AttributeError, IndexError):
            pass
        return 19

    @staticmethod
    def _hour_focus_factor(start_hour: int) -> float:
        if 5 <= start_hour < 10:
            return 1.12
        if 10 <= start_hour < 14:
            return 1.0
        if 14 <= start_hour < 18:
            return 0.93
        if 18 <= start_hour < 22:
            return 1.08
        return 0.88

    @staticmethod
    def _performance_factor(db: Session, user_id: int, organization_id: int) -> tuple[float, dict]:
        window_start = date.today() - timedelta(days=14)
        rows = (
            db.query(Performance)
            .filter(
                Performance.user_id == user_id,
                Performance.organization_id == organization_id,
                Performance.date >= window_start,
            )
            .all()
        )
        if not rows:
            return 1.0, {"entries": 0, "avg_productivity": 0.0, "consistency": 0.0}

        avg_productivity = mean(item.productivity_index for item in rows)
        if avg_productivity <= 1:
            avg_productivity *= 100
        avg_productivity = max(0.0, min(avg_productivity, 100.0))
        consistency = sum(1 for item in rows if item.completed_tasks > 0) / len(rows)
        factor = 0.8 + (avg_productivity / 100.0) * 0.35 + consistency * 0.2
        factor = max(0.75, min(1.35, factor))
        return factor, {
            "entries": len(rows),
            "avg_productivity": round(avg_productivity, 2),
            "consistency": round(consistency, 2),
        }

    @staticmethod
    def _task_cognitive_load(subject: Subject, estimated_time: int, is_review: bool = False) -> float:
        base = estimated_time / 30
        difficulty_weight = 0.6 + (subject.difficulty * 0.25)
        review_discount = 0.72 if is_review else 1.0
        return round(base * difficulty_weight * review_discount, 2)

    @staticmethod
    def generate_daily_plan(
        db: Session,
        user_id: int,
        organization_id: int,
        available_minutes: int,
        time_block_override: str | None = None,
    ) -> dict:
        user = db.get(User, user_id)
        if not user:
            return {"detail": "User not found"}

        planning_time_block = time_block_override or user.preferred_time_block
        start_hour = StudyEngine._extract_start_hour(planning_time_block)
        hour_factor = StudyEngine._hour_focus_factor(start_hour)
        perf_factor, perf_meta = StudyEngine._performance_factor(db, user_id, organization_id)
        cognitive_budget = round((available_minutes / 30) * hour_factor * perf_factor, 2)
        review_load_cap = round(cognitive_budget * 0.45, 2)
        review_time_cap = int(available_minutes * 0.5)

        due_reviews = (
            db.query(Review)
            .join(Task, Task.id == Review.task_id)
            .join(Subject, Subject.id == Task.subject_id)
            .filter(
                Subject.user_id == user_id,
                Subject.organization_id == organization_id,
                Review.next_review_date <= date.today(),
            )
            .all()
        )
        review_task_ids = {review.task_id for review in due_reviews}
        review_candidates = (
            db.query(Task, Subject, Review)
            .join(Subject, Task.subject_id == Subject.id)
            .join(Review, Review.task_id == Task.id)
            .filter(
                Subject.user_id == user_id,
                Subject.organization_id == organization_id,
                Review.next_review_date <= date.today(),
            )
            .all()
        )

        def review_priority(item: tuple[Task, Subject, Review]) -> float:
            task, subject, review = item
            overdue_days = max(0, (date.today() - review.next_review_date).days)
            retention_gap = 100 - task.mastery_level
            return (overdue_days * 1.2) + (retention_gap * 0.3) + (subject.importance_level * 1.5)

        review_candidates = sorted(review_candidates, key=review_priority, reverse=True)
        selected_reviews = []
        used_review_minutes = 0
        used_review_load = 0.0
        for task, subject, review in review_candidates:
            item_minutes = task.estimated_time
            item_load = StudyEngine._task_cognitive_load(
                subject=subject, estimated_time=task.estimated_time, is_review=True
            )
            if used_review_minutes + item_minutes > review_time_cap:
                continue
            if used_review_load + item_load > review_load_cap:
                continue
            selected_reviews.append((task, subject, review, item_load))
            used_review_minutes += item_minutes
            used_review_load += item_load

        candidates = (
            db.query(Task, Subject)
            .join(Subject, Task.subject_id == Subject.id)
            .filter(Subject.user_id == user_id, Subject.organization_id == organization_id, Task.status != "done")
            .all()
        )
        ranked = sorted(
            [
                {
                    "task_id": task.id,
                    "title": task.title,
                    "subject": subject.name,
                    "category": subject.category,
                    "difficulty": subject.difficulty,
                    "estimated_time": task.estimated_time,
                    "priority_score": ParetoEngine.priority_score(subject, task),
                    "cognitive_load": StudyEngine._task_cognitive_load(
                        subject=subject, estimated_time=task.estimated_time
                    ),
                }
                for task, subject in candidates
                if task.id not in review_task_ids
            ],
            key=lambda item: item["priority_score"],
            reverse=True,
        )

        minutes_left = available_minutes - used_review_minutes
        cognitive_left = cognitive_budget - used_review_load
        selected_new: list[dict] = []
        category_counts: dict[str, int] = {}
        available_categories = {item["category"] for item in ranked}
        category_target = (
            max(1, ceil((available_minutes / 45) / len(available_categories)))
            if available_categories
            else 1
        )

        while ranked and minutes_left > 0 and cognitive_left > 0:
            best_index = None
            best_score = -1.0
            for idx, item in enumerate(ranked):
                if item["estimated_time"] > minutes_left:
                    continue
                if item["cognitive_load"] > cognitive_left:
                    continue

                category = item["category"]
                current_count = category_counts.get(category, 0)
                category_penalty = 1 + (current_count * 0.35)
                if current_count >= category_target:
                    category_penalty += 0.25

                contextual_score = item["priority_score"] / category_penalty
                if best_index is None or contextual_score > best_score:
                    best_index = idx
                    best_score = contextual_score

            if best_index is None:
                break

            chosen = ranked.pop(best_index)
            selected_new.append(chosen)
            minutes_left -= chosen["estimated_time"]
            cognitive_left -= chosen["cognitive_load"]
            category = chosen["category"]
            category_counts[category] = category_counts.get(category, 0) + 1

        review_items = [
            {
                "task_id": task.id,
                "title": task.title,
                "subject": subject.name,
                "category": subject.category,
                "estimated_time": task.estimated_time,
                "cognitive_load": item_load,
                "review_interval_days": review.interval,
                "type": "review",
            }
            for task, subject, review, item_load in selected_reviews
        ]

        return {
            "date": str(date.today()),
            "available_minutes": available_minutes,
            "time_block": planning_time_block,
            "scheduled_reviews": review_items,
            "scheduled_new_tasks": selected_new,
            "unused_minutes": minutes_left,
            "unused_cognitive_budget": round(max(cognitive_left, 0), 2),
            "planning_context": {
                "hour_focus_factor": hour_factor,
                "performance_factor": perf_factor,
                "cognitive_budget": cognitive_budget,
                "review_load_cap": review_load_cap,
                "review_time_cap_minutes": review_time_cap,
                "performance_window": perf_meta,
                "category_distribution": category_counts,
            },
        }
