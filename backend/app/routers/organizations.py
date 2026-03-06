import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_permission
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberInvite,
    OrganizationMemberListResponse,
    OrganizationMemberOut,
    OrganizationMemberRoleUpdate,
    OrganizationOut,
)
from app.services.study_event_service import StudyEventService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/", response_model=list[OrganizationOut])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:list")),
) -> list[dict]:
    rows = (
        db.query(Organization, Membership)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == current_user.id)
        .all()
    )
    return [
        {"id": org.id, "name": org.name, "slug": org.slug, "role": member.role}
        for org, member in rows
    ]


@router.post("/", response_model=OrganizationOut)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:create")),
) -> dict:
    slug_base = payload.name.strip().lower().replace(" ", "-")
    slug_base = "".join(ch for ch in slug_base if ch.isalnum() or ch == "-").strip("-") or "workspace"
    slug = slug_base
    i = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        i += 1
        slug = f"{slug_base}-{i}"

    org = Organization(name=payload.name.strip(), slug=slug)
    db.add(org)
    db.flush()

    exists = (
        db.query(Membership)
        .filter(Membership.user_id == current_user.id, Membership.organization_id == org.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Membership already exists")

    member = Membership(user_id=current_user.id, organization_id=org.id, role="owner")
    db.add(member)
    db.commit()
    StudyEventService.record(
        db=db,
        organization_id=org.id,
        user_id=current_user.id,
        event_type="organization.created",
        entity_type="organization",
        entity_id=str(org.id),
        payload={"name": org.name, "slug": org.slug},
        commit=True,
    )
    return {"id": org.id, "name": org.name, "slug": org.slug, "role": member.role}


def _get_org_membership(db: Session, organization_id: int, user_id: int) -> Membership:
    membership = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Organization access denied")
    return membership


def _assert_org_exists(db: Session, organization_id: int) -> None:
    if not db.get(Organization, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")


def _assert_manager_role(role: str) -> None:
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Insufficient organization role")


@router.get("/{organization_id}/members", response_model=OrganizationMemberListResponse)
def list_members(
    organization_id: int,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    role: str | None = Query(default=None, pattern="^(owner|admin|member)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["email", "role", "created_at"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:members:list")),
) -> dict:
    _assert_org_exists(db, organization_id)
    _get_org_membership(db, organization_id, current_user.id)

    query = (
        db.query(Membership, User.email)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.organization_id == organization_id)
    )
    if role:
        query = query.filter(Membership.role == role.lower())
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            (func.lower(User.email).like(term))
            | (cast(Membership.user_id, String).like(term))
            | (func.lower(Membership.role).like(term))
        )

    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    sort_column_map = {
        "email": User.email,
        "role": Membership.role,
        "created_at": Membership.created_at,
    }
    order_column = sort_column_map[sort_by]
    if sort_dir == "asc":
        query = query.order_by(order_column.asc(), Membership.id.asc())
    else:
        query = query.order_by(order_column.desc(), Membership.id.desc())

    rows = query.offset(offset).limit(page_size).all()
    items = [{"user_id": member.user_id, "email": email, "role": member.role} for member, email in rows]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("/{organization_id}/members/invite", response_model=OrganizationMemberOut)
def invite_member(
    organization_id: int,
    payload: OrganizationMemberInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:members:invite")),
) -> dict:
    _assert_org_exists(db, organization_id)
    actor = _get_org_membership(db, organization_id, current_user.id)
    _assert_manager_role(actor.role.lower())

    requested_role = payload.role.lower()
    if actor.role.lower() == "admin" and requested_role == "owner":
        raise HTTPException(status_code=403, detail="Admin cannot assign owner role")

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.user_id == user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this organization")

    member = Membership(user_id=user.id, organization_id=organization_id, role=requested_role)
    db.add(member)
    db.commit()
    StudyEventService.record(
        db=db,
        organization_id=organization_id,
        user_id=current_user.id,
        event_type="organization.member.invited",
        entity_type="membership",
        entity_id=str(member.id),
        payload={"invited_user_id": user.id, "invited_email": user.email, "role": requested_role},
        commit=True,
    )
    return {"user_id": user.id, "email": user.email, "role": member.role}


@router.patch("/{organization_id}/members/{member_user_id}/role", response_model=OrganizationMemberOut)
def update_member_role(
    organization_id: int,
    member_user_id: int,
    payload: OrganizationMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:members:update_role")),
) -> dict:
    _assert_org_exists(db, organization_id)
    actor = _get_org_membership(db, organization_id, current_user.id)
    _assert_manager_role(actor.role.lower())

    if current_user.id == member_user_id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")

    target = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.user_id == member_user_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found")

    new_role = payload.role.lower()
    actor_role = actor.role.lower()
    target_role = target.role.lower()

    if actor_role == "admin":
        if target_role == "owner":
            raise HTTPException(status_code=403, detail="Admin cannot modify owner")
        if new_role == "owner":
            raise HTTPException(status_code=403, detail="Admin cannot assign owner role")

    if target_role == "owner" and new_role != "owner":
        owner_count = (
            db.query(Membership)
            .filter(Membership.organization_id == organization_id, Membership.role == "owner")
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Organization must have at least one owner")

    target.role = new_role
    db.commit()
    StudyEventService.record(
        db=db,
        organization_id=organization_id,
        user_id=current_user.id,
        event_type="organization.member.role_updated",
        entity_type="membership",
        entity_id=str(target.id),
        payload={"target_user_id": member_user_id, "new_role": new_role},
        commit=True,
    )

    user = db.get(User, member_user_id)
    return {"user_id": member_user_id, "email": user.email if user else "", "role": target.role}


@router.delete("/{organization_id}/members/{member_user_id}", status_code=204)
def remove_member(
    organization_id: int,
    member_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Membership = Depends(require_permission("organizations:members:remove")),
) -> Response:
    _assert_org_exists(db, organization_id)
    actor = _get_org_membership(db, organization_id, current_user.id)
    _assert_manager_role(actor.role.lower())

    if current_user.id == member_user_id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself from organization")

    target = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.user_id == member_user_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found")

    actor_role = actor.role.lower()
    target_role = target.role.lower()
    if actor_role == "admin" and target_role == "owner":
        raise HTTPException(status_code=403, detail="Admin cannot remove owner")

    if target_role == "owner":
        owner_count = (
            db.query(Membership)
            .filter(Membership.organization_id == organization_id, Membership.role == "owner")
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Organization must have at least one owner")

    target_id = target.id
    target_user_id = target.user_id
    db.delete(target)
    db.commit()
    StudyEventService.record(
        db=db,
        organization_id=organization_id,
        user_id=current_user.id,
        event_type="organization.member.removed",
        entity_type="membership",
        entity_id=str(target_id),
        payload={"target_user_id": target_user_id},
        commit=True,
    )
    return Response(status_code=204)
