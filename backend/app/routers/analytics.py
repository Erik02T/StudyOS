from datetime import date
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.study_event import StudyEvent
from app.models.user import User
from app.schemas.analytics import (
    PerformanceLogRequest,
    PerformanceLogResponse,
    StudyEventListResponse,
    StudyEventOut,
)
from app.services.analytics_engine import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("analytics:view")),
) -> dict:
    return AnalyticsEngine.summary_for_user(db, current_user.id, current_org.id, days=days)


@router.post("/performance", response_model=PerformanceLogResponse)
def log_performance(
    payload: PerformanceLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("analytics:write")),
) -> object:
    if payload.accumulate:
        performance = AnalyticsEngine.accumulate_performance(
            db=db,
            user_id=current_user.id,
            organization_id=current_org.id,
            record_date=payload.date or date.today(),
            completed_tasks_delta=payload.completed_tasks,
            study_minutes_delta=payload.study_minutes,
            focus_score=payload.focus_score,
            productivity_index=payload.productivity_index,
            time_block=payload.time_block or current_user.preferred_time_block,
        )
    else:
        performance = AnalyticsEngine.record_performance(
            db=db,
            user_id=current_user.id,
            organization_id=current_org.id,
            record_date=payload.date or date.today(),
            completed_tasks=payload.completed_tasks,
            study_minutes=payload.study_minutes,
            focus_score=payload.focus_score,
            productivity_index=payload.productivity_index,
            time_block=payload.time_block or current_user.preferred_time_block,
        )
    return performance


@router.get("/heatmap")
def get_heatmap(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("analytics:view")),
) -> dict:
    return AnalyticsEngine.heatmap_for_user(db, current_user.id, current_org.id, days=days)


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("analytics:view")),
) -> dict:
    return AnalyticsEngine.dashboard_for_user(db, current_user.id, current_org.id, days=days)


@router.get("/events", response_model=StudyEventListResponse)
def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    event_type: str | None = Query(default=None, max_length=80),
    user_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("audit:events:view")),
) -> StudyEventListResponse:
    query = db.query(StudyEvent).filter(StudyEvent.organization_id == current_org.id)
    if event_type:
        query = query.filter(StudyEvent.event_type == event_type)
    if user_id:
        query = query.filter(StudyEvent.user_id == user_id)

    total = query.count()
    pages = max(1, (total + page_size - 1) // page_size)
    rows = (
        query.order_by(StudyEvent.created_at.desc(), StudyEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: list[StudyEventOut] = []
    for row in rows:
        payload = None
        if row.payload_json:
            try:
                payload = json.loads(row.payload_json)
            except json.JSONDecodeError:
                payload = {"raw": row.payload_json}
        items.append(
            StudyEventOut(
                id=row.id,
                organization_id=row.organization_id,
                user_id=row.user_id,
                event_type=row.event_type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                payload=payload,
                created_at=row.created_at,
            )
        )

    return StudyEventListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)
