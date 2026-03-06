from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.review import ReviewAnswerRequest, ReviewAnswerResponse, ReviewDueItem
from app.services.review_service import ReviewService
from app.services.study_event_service import StudyEventService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/due", response_model=list[ReviewDueItem])
def get_due_reviews(
    for_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("reviews:list")),
) -> list[dict]:
    return ReviewService.get_due_reviews(
        db=db, user_id=current_user.id, organization_id=current_org.id, for_date=for_date
    )


@router.post("/answer", response_model=ReviewAnswerResponse)
def answer_review(
    payload: ReviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("reviews:answer")),
) -> dict:
    result = ReviewService.answer_review(
        db=db,
        user_id=current_user.id,
        organization_id=current_org.id,
        task_id=payload.task_id,
        quality=payload.quality,
        review_date=payload.review_date,
    )
    StudyEventService.record(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        event_type="review.answered",
        entity_type="task",
        entity_id=str(payload.task_id),
        payload={"quality": payload.quality, "review_date": str(payload.review_date or date.today())},
        commit=True,
    )
    return result
