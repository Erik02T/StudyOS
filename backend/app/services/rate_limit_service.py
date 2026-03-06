import datetime as dt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.rate_limit_event import RateLimitEvent


class RateLimitService:
    @staticmethod
    def hit(
        db: Session,
        identifier: str,
        endpoint: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        now = dt.datetime.utcnow()
        window_start = now - dt.timedelta(seconds=window_seconds)

        db.query(RateLimitEvent).filter(RateLimitEvent.created_at < window_start).delete()

        current_count = (
            db.query(RateLimitEvent)
            .filter(
                RateLimitEvent.identifier == identifier,
                RateLimitEvent.endpoint == endpoint,
                RateLimitEvent.created_at >= window_start,
            )
            .count()
        )
        if current_count >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        db.add(RateLimitEvent(identifier=identifier, endpoint=endpoint, created_at=now))
        db.commit()

