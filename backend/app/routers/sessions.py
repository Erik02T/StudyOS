from datetime import date
import datetime as dt
import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.idempotency_key import IdempotencyKey
from app.models.organization import Organization
from app.models.user import User
from app.schemas.session import SessionFinalizeRequest, SessionFinalizeResponse
from app.services.analytics_engine import AnalyticsEngine
from app.services.study_event_service import StudyEventService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/finalize", response_model=SessionFinalizeResponse)
def finalize_session(
    payload: SessionFinalizeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("sessions:finalize")),
) -> dict:
    endpoint_name = "sessions:finalize"
    payload_hash = hashlib.sha256(payload.model_dump_json().encode("utf-8")).hexdigest()
    idempotency_row: IdempotencyKey | None = None
    if idempotency_key:
        existing = (
            db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.user_id == current_user.id,
                IdempotencyKey.organization_id == current_org.id,
                IdempotencyKey.endpoint == endpoint_name,
                IdempotencyKey.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            if existing.request_hash != payload_hash:
                raise HTTPException(status_code=409, detail="Idempotency key already used with different payload")
            if existing.response_body and existing.status_code == 200:
                try:
                    return json.loads(existing.response_body)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Stored idempotent response is invalid")
            raise HTTPException(status_code=409, detail="Request with this idempotency key is in progress")

        idempotency_row = IdempotencyKey(
            user_id=current_user.id,
            organization_id=current_org.id,
            endpoint=endpoint_name,
            idempotency_key=idempotency_key,
            request_hash=payload_hash,
        )
        db.add(idempotency_row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            duplicate = (
                db.query(IdempotencyKey)
                .filter(
                    IdempotencyKey.user_id == current_user.id,
                    IdempotencyKey.organization_id == current_org.id,
                    IdempotencyKey.endpoint == endpoint_name,
                    IdempotencyKey.idempotency_key == idempotency_key,
                )
                .first()
            )
            if duplicate and duplicate.request_hash == payload_hash and duplicate.response_body and duplicate.status_code == 200:
                return json.loads(duplicate.response_body)
            raise HTTPException(status_code=409, detail="Idempotency key conflict")

    quality = payload.quality
    completed_tasks = (
        payload.completed_tasks
        if payload.completed_tasks is not None
        else (1 if quality is not None and quality >= 3 else 0)
    )
    focus_score = (
        payload.focus_score
        if payload.focus_score is not None
        else (45 + quality * 10 if quality is not None else 70)
    )
    focus_score = max(0, min(float(focus_score), 100))

    performance = AnalyticsEngine.accumulate_performance(
        db=db,
        user_id=current_user.id,
        organization_id=current_org.id,
        record_date=payload.date or date.today(),
        completed_tasks_delta=completed_tasks,
        study_minutes_delta=payload.study_minutes,
        focus_score=focus_score,
        productivity_index=payload.productivity_index,
        time_block=payload.time_block or current_user.preferred_time_block,
    )
    response_payload = {
        "message": "Session finalized and analytics updated",
        "source": payload.source,
        "performance_id": performance.id,
        "date": performance.date,
        "completed_tasks": performance.completed_tasks,
        "study_minutes": performance.study_minutes,
        "focus_score": performance.focus_score,
        "productivity_index": performance.productivity_index,
        "time_block": performance.time_block,
    }
    StudyEventService.record(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        event_type="session.finalized",
        entity_type="performance",
        entity_id=str(performance.id),
        payload={
            "source": payload.source,
            "date": str(performance.date),
            "study_minutes": performance.study_minutes,
            "completed_tasks": performance.completed_tasks,
        },
        commit=True,
    )
    if idempotency_row:
        idempotency_row.response_body = json.dumps(response_payload, default=str)
        idempotency_row.status_code = 200
        idempotency_row.completed_at = dt.datetime.utcnow()
        db.commit()
    return response_payload
