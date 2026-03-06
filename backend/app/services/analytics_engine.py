from datetime import date, timedelta
from statistics import mean

from sqlalchemy.orm import Session

from app.models.performance import Performance
from app.models.subject import Subject
from app.models.task import Task
from app.models.user import User


class AnalyticsEngine:
    @staticmethod
    def _normalize_productivity(value: float) -> float:
        if value <= 1:
            value *= 100
        return round(max(0.0, min(value, 100.0)), 2)

    @staticmethod
    def _derive_productivity(completed_tasks: int, focus_score: float, study_minutes: int) -> float:
        task_factor = min(completed_tasks * 12, 40)
        focus_factor = min(max(focus_score, 0), 100) * 0.4
        time_factor = min(study_minutes / 3, 25)
        return round(min(task_factor + focus_factor + time_factor, 100.0), 2)

    @staticmethod
    def _parse_start_hour(time_block: str | None) -> int:
        if not time_block:
            return 12
        try:
            raw = time_block.split("-")[0].split(":")[0]
            hour = int(raw)
            if 0 <= hour <= 23:
                return hour
        except (ValueError, AttributeError, IndexError):
            pass
        return 12

    @staticmethod
    def _time_bucket(time_block: str | None) -> str:
        hour = AnalyticsEngine._parse_start_hour(time_block)
        if 5 <= hour < 10:
            return "morning"
        if 10 <= hour < 14:
            return "late_morning"
        if 14 <= hour < 18:
            return "afternoon"
        if 18 <= hour < 22:
            return "evening"
        return "late_night"

    @staticmethod
    def _streaks(rows: list[Performance]) -> tuple[int, int]:
        if not rows:
            return 0, 0

        active_dates = sorted({row.date for row in rows if row.completed_tasks > 0 or row.study_minutes > 0})
        if not active_dates:
            return 0, 0

        best_streak = 1
        current_run = 1
        for idx in range(1, len(active_dates)):
            if (active_dates[idx] - active_dates[idx - 1]).days == 1:
                current_run += 1
                best_streak = max(best_streak, current_run)
            else:
                current_run = 1

        current_streak = 0
        cursor = date.today()
        active_lookup = set(active_dates)
        while cursor in active_lookup:
            current_streak += 1
            cursor -= timedelta(days=1)

        return current_streak, best_streak

    @staticmethod
    def record_performance(
        db: Session,
        user_id: int,
        organization_id: int,
        record_date: date,
        completed_tasks: int,
        study_minutes: int,
        focus_score: float,
        productivity_index: float | None,
        time_block: str,
    ) -> Performance:
        row = (
            db.query(Performance)
            .filter(
                Performance.user_id == user_id,
                Performance.organization_id == organization_id,
                Performance.date == record_date,
            )
            .first()
        )
        normalized_productivity = (
            AnalyticsEngine._normalize_productivity(productivity_index)
            if productivity_index is not None
            else AnalyticsEngine._derive_productivity(completed_tasks, focus_score, study_minutes)
        )
        if row:
            row.completed_tasks = completed_tasks
            row.study_minutes = study_minutes
            row.focus_score = round(focus_score, 2)
            row.productivity_index = normalized_productivity
            row.time_block = time_block
        else:
            row = Performance(
                user_id=user_id,
                organization_id=organization_id,
                date=record_date,
                completed_tasks=completed_tasks,
                study_minutes=study_minutes,
                focus_score=round(focus_score, 2),
                productivity_index=normalized_productivity,
                time_block=time_block,
            )
            db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def accumulate_performance(
        db: Session,
        user_id: int,
        organization_id: int,
        record_date: date,
        completed_tasks_delta: int,
        study_minutes_delta: int,
        focus_score: float,
        productivity_index: float | None,
        time_block: str,
    ) -> Performance:
        row = (
            db.query(Performance)
            .filter(
                Performance.user_id == user_id,
                Performance.organization_id == organization_id,
                Performance.date == record_date,
            )
            .first()
        )
        incoming_productivity = (
            AnalyticsEngine._normalize_productivity(productivity_index)
            if productivity_index is not None
            else AnalyticsEngine._derive_productivity(
                completed_tasks=completed_tasks_delta,
                focus_score=focus_score,
                study_minutes=study_minutes_delta,
            )
        )

        if row:
            prev_minutes = max(row.study_minutes, 0)
            new_minutes = max(study_minutes_delta, 0)
            total_minutes = prev_minutes + new_minutes

            row.completed_tasks = max(0, row.completed_tasks + completed_tasks_delta)
            row.study_minutes = total_minutes
            row.time_block = time_block or row.time_block

            if total_minutes > 0:
                weighted_focus = ((row.focus_score * prev_minutes) + (focus_score * new_minutes)) / total_minutes
                row.focus_score = round(weighted_focus, 2)
                weighted_productivity = (
                    (row.productivity_index * prev_minutes) + (incoming_productivity * new_minutes)
                ) / total_minutes
                row.productivity_index = round(weighted_productivity, 2)
            else:
                row.focus_score = round((row.focus_score + focus_score) / 2, 2)
                row.productivity_index = round((row.productivity_index + incoming_productivity) / 2, 2)
        else:
            row = Performance(
                user_id=user_id,
                organization_id=organization_id,
                date=record_date,
                completed_tasks=max(0, completed_tasks_delta),
                study_minutes=max(0, study_minutes_delta),
                focus_score=round(focus_score, 2),
                productivity_index=incoming_productivity,
                time_block=time_block,
            )
            db.add(row)

        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def _fetch_rows(db: Session, user_id: int, organization_id: int, days: int) -> list[Performance]:
        start_date = date.today() - timedelta(days=max(1, days) - 1)
        return (
            db.query(Performance)
            .filter(
                Performance.user_id == user_id,
                Performance.organization_id == organization_id,
                Performance.date >= start_date,
            )
            .order_by(Performance.date.asc())
            .all()
        )

    @staticmethod
    def summary_for_user(db: Session, user_id: int, organization_id: int, days: int = 30) -> dict:
        rows = AnalyticsEngine._fetch_rows(db=db, user_id=user_id, organization_id=organization_id, days=days)
        if not rows:
            return {
                "window_days": days,
                "entries": 0,
                "avg_completed_tasks": 0.0,
                "avg_study_minutes": 0.0,
                "avg_focus_score": 0.0,
                "avg_productivity_index": 0.0,
            }
        return {
            "window_days": days,
            "entries": len(rows),
            "avg_completed_tasks": round(mean(r.completed_tasks for r in rows), 2),
            "avg_study_minutes": round(mean(r.study_minutes for r in rows), 2),
            "avg_focus_score": round(mean(r.focus_score for r in rows), 2),
            "avg_productivity_index": round(mean(r.productivity_index for r in rows), 2),
        }

    @staticmethod
    def heatmap_for_user(db: Session, user_id: int, organization_id: int, days: int = 30) -> dict:
        rows = AnalyticsEngine._fetch_rows(db=db, user_id=user_id, organization_id=organization_id, days=days)
        buckets: dict[str, list[Performance]] = {}
        for row in rows:
            bucket = AnalyticsEngine._time_bucket(row.time_block)
            buckets.setdefault(bucket, []).append(row)

        heatmap = []
        for bucket_name in ["morning", "late_morning", "afternoon", "evening", "late_night"]:
            bucket_rows = buckets.get(bucket_name, [])
            if not bucket_rows:
                heatmap.append(
                    {
                        "bucket": bucket_name,
                        "sessions": 0,
                        "avg_productivity_index": 0.0,
                        "avg_focus_score": 0.0,
                    }
                )
                continue
            heatmap.append(
                {
                    "bucket": bucket_name,
                    "sessions": len(bucket_rows),
                    "avg_productivity_index": round(mean(r.productivity_index for r in bucket_rows), 2),
                    "avg_focus_score": round(mean(r.focus_score for r in bucket_rows), 2),
                }
            )

        best = max(heatmap, key=lambda x: x["avg_productivity_index"])
        return {"window_days": days, "heatmap": heatmap, "best_time_bucket": best["bucket"]}

    @staticmethod
    def dashboard_for_user(db: Session, user_id: int, organization_id: int, days: int = 30) -> dict:
        user = db.get(User, user_id)
        rows = AnalyticsEngine._fetch_rows(db=db, user_id=user_id, organization_id=organization_id, days=days)
        summary = AnalyticsEngine.summary_for_user(
            db=db, user_id=user_id, organization_id=organization_id, days=days
        )
        heatmap = AnalyticsEngine.heatmap_for_user(
            db=db, user_id=user_id, organization_id=organization_id, days=days
        )

        active_days = sum(1 for r in rows if r.completed_tasks > 0 or r.study_minutes > 0)
        consistency_rate = round((active_days / max(days, 1)) * 100, 2)
        current_streak, best_streak = AnalyticsEngine._streaks(rows)

        trend = [
            {
                "date": str(r.date),
                "completed_tasks": r.completed_tasks,
                "study_minutes": r.study_minutes,
                "focus_score": r.focus_score,
                "productivity_index": r.productivity_index,
            }
            for r in rows
        ]

        total_tasks = (
            db.query(Task)
            .join(Subject, Task.subject_id == Subject.id)
            .filter(Subject.user_id == user_id, Subject.organization_id == organization_id)
            .count()
        )
        completed_tasks = (
            db.query(Task)
            .join(Subject, Task.subject_id == Subject.id)
            .filter(Subject.user_id == user_id, Subject.organization_id == organization_id, Task.status == "done")
            .count()
        )
        completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0.0

        evolution_score = round(
            (consistency_rate * 0.35)
            + (summary["avg_productivity_index"] * 0.4)
            + (completion_rate * 0.25),
            2,
        )

        insight = (
            f"Seu melhor bloco recente e {heatmap['best_time_bucket']}. "
            f"Consistencia em {consistency_rate}% nos ultimos {days} dias."
        )

        return {
            "user_email": user.email if user else None,
            "window_days": days,
            "summary": summary,
            "consistency": {
                "active_days": active_days,
                "consistency_rate": consistency_rate,
                "current_streak": current_streak,
                "best_streak": best_streak,
            },
            "progress": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "evolution_score": evolution_score,
            },
            "heatmap": heatmap,
            "trend": trend,
            "insight": insight,
        }
