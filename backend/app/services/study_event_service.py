import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.study_event import StudyEvent


class StudyEventService:
    @staticmethod
    def record(
        db: Session,
        *,
        organization_id: int,
        user_id: int | None,
        event_type: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        payload: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> StudyEvent:
        event = StudyEvent(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload, default=str) if payload is not None else None,
        )
        db.add(event)
        if commit:
            db.commit()
            db.refresh(event)
        return event
