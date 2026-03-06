from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_organization, get_current_user, require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectOut, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("/", response_model=SubjectOut)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("subjects:create")),
) -> Subject:
    subject = Subject(user_id=current_user.id, organization_id=current_org.id, **payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("subjects:list")),
) -> list[Subject]:
    return (
        db.query(Subject)
        .filter(Subject.user_id == current_user.id, Subject.organization_id == current_org.id)
        .all()
    )


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("subjects:update")),
) -> Subject:
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
            Subject.organization_id == current_org.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, key, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("subjects:delete")),
) -> None:
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
            Subject.organization_id == current_org.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()
    return None
