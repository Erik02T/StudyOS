from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.review import Review
from app.models.subject import Subject
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.billing_service import BillingService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("tasks:create")),
) -> Task:
    BillingService.check_and_consume(
        db=db,
        organization_id=current_org.id,
        metric=BillingService.METRIC_TASKS_CREATED,
        amount=1,
    )
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == payload.subject_id,
            Subject.user_id == current_user.id,
            Subject.organization_id == current_org.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    task = Task(**payload.model_dump())
    db.add(task)
    db.flush()
    ReviewService.ensure_review_for_task(db=db, task_id=task.id, start_date=date.today())
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("tasks:list")),
) -> list[Task]:
    return (
        db.query(Task)
        .join(Subject, Task.subject_id == Subject.id)
        .filter(Subject.user_id == current_user.id, Subject.organization_id == current_org.id)
        .all()
    )


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("tasks:update")),
) -> Task:
    task = (
        db.query(Task)
        .join(Subject, Task.subject_id == Subject.id)
        .filter(Task.id == task_id, Subject.user_id == current_user.id, Subject.organization_id == current_org.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_status = task.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    should_init_review = previous_status != "done" and task.status == "done"
    if should_init_review:
        existing_review = db.query(Review).filter(Review.task_id == task.id).first()
        if not existing_review:
            ReviewService.ensure_review_for_task(db=db, task_id=task.id, start_date=date.today())

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("tasks:delete")),
) -> None:
    task = (
        db.query(Task)
        .join(Subject, Task.subject_id == Subject.id)
        .filter(Task.id == task_id, Subject.user_id == current_user.id, Subject.organization_id == current_org.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
