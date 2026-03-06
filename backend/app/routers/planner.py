from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.planner import GeneratePlanRequest
from app.services.study_engine import StudyEngine

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/generate-plan")
def generate_plan(
    payload: GeneratePlanRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("planner:generate")),
) -> dict:
    available_minutes = (
        payload.available_minutes
        if payload and payload.available_minutes is not None
        else current_user.available_hours_per_day * 60
    )
    time_block = payload.time_block if payload else None
    return StudyEngine.generate_daily_plan(
        db=db,
        user_id=current_user.id,
        organization_id=current_org.id,
        available_minutes=available_minutes,
        time_block_override=time_block,
    )
