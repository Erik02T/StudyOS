from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.session import SessionFinalizeRequest, SessionFinalizeResponse
from app.services.analytics_engine import AnalyticsEngine

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/finalize", response_model=SessionFinalizeResponse)
def finalize_session(
    payload: SessionFinalizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("sessions:finalize")),
) -> dict:
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
    return {
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
