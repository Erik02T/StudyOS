from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.db.session import get_db
from app.models.membership import Membership
from app.services.email_queue_service import EmailQueueService

router = APIRouter(prefix="/internal/email-queue", tags=["internal-email-queue"])


@router.get("/stats")
def get_email_queue_stats(
    db: Session = Depends(get_db),
    membership: Membership = Depends(require_permission("internal:email_queue:view")),
) -> dict:
    _ = membership
    return EmailQueueService.stats(db=db)


@router.post("/process")
def process_email_queue(
    batch_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    membership: Membership = Depends(require_permission("internal:email_queue:process")),
) -> dict:
    _ = membership
    result = EmailQueueService.process_pending(db=db, batch_size=batch_size)
    result["stats"] = EmailQueueService.stats(db=db)
    return result
