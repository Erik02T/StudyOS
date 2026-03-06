from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.subject import Subject
from app.models.task import Task
from app.services.spaced_repetition import SpacedRepetitionEngine


class ReviewService:
    @staticmethod
    def ensure_review_for_task(db: Session, task_id: int, start_date: date | None = None) -> Review:
        review = db.query(Review).filter(Review.task_id == task_id).first()
        if review:
            return review

        base_date = start_date or date.today()
        review = Review(
            task_id=task_id,
            next_review_date=base_date + timedelta(days=1),
            interval=0,
            ease_factor=2.5,
        )
        db.add(review)
        db.flush()
        return review

    @staticmethod
    def get_due_reviews(
        db: Session, user_id: int, organization_id: int, for_date: date | None = None
    ) -> list[dict]:
        target_date = for_date or date.today()
        rows = (
            db.query(Task, Subject, Review)
            .join(Subject, Task.subject_id == Subject.id)
            .join(Review, Review.task_id == Task.id)
            .filter(
                Subject.user_id == user_id,
                Subject.organization_id == organization_id,
                Review.next_review_date <= target_date,
            )
            .order_by(Review.next_review_date.asc())
            .all()
        )
        return [
            {
                "task_id": task.id,
                "title": task.title,
                "subject": subject.name,
                "category": subject.category,
                "estimated_time": task.estimated_time,
                "next_review_date": review.next_review_date,
                "interval": review.interval,
                "ease_factor": round(review.ease_factor, 2),
                "mastery_level": task.mastery_level,
            }
            for task, subject, review in rows
        ]

    @staticmethod
    def answer_review(
        db: Session,
        user_id: int,
        organization_id: int,
        task_id: int,
        quality: int,
        review_date: date | None = None,
    ) -> dict:
        row = (
            db.query(Task, Subject)
            .join(Subject, Task.subject_id == Subject.id)
            .filter(Task.id == task_id, Subject.user_id == user_id, Subject.organization_id == organization_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        task, _subject = row

        review = ReviewService.ensure_review_for_task(db=db, task_id=task.id, start_date=review_date)

        previous_interval = review.interval
        previous_ease = review.ease_factor
        previous_mastery = task.mastery_level

        new_interval, new_ease = SpacedRepetitionEngine.sm2(
            interval=review.interval,
            ease_factor=review.ease_factor,
            quality=quality,
        )
        effective_date = review_date or date.today()
        next_date = SpacedRepetitionEngine.next_review_date(effective_date, new_interval)

        review.interval = new_interval
        review.ease_factor = round(new_ease, 2)
        review.next_review_date = next_date

        mastery_delta = (quality - 2) * 8
        if quality < 3:
            mastery_delta -= 4
        task.mastery_level = max(0, min(100, task.mastery_level + mastery_delta))
        task.status = "done" if task.mastery_level >= 85 else "in_progress"

        db.commit()
        db.refresh(review)
        db.refresh(task)

        return {
            "task_id": task.id,
            "quality": quality,
            "previous_interval": previous_interval,
            "new_interval": review.interval,
            "previous_ease_factor": round(previous_ease, 2),
            "new_ease_factor": round(review.ease_factor, 2),
            "previous_mastery_level": previous_mastery,
            "new_mastery_level": task.mastery_level,
            "next_review_date": review.next_review_date,
        }
