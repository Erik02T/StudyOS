import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.revoked_token import RevokedToken
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ROLE_PERMISSIONS = {
    "owner": {"*"},
    "admin": {
        "organizations:list",
        "organizations:create",
        "organizations:members:list",
        "organizations:members:invite",
        "organizations:members:update_role",
        "organizations:members:remove",
        "subjects:list",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "tasks:list",
        "tasks:create",
        "tasks:update",
        "tasks:delete",
        "planner:generate",
        "reviews:list",
        "reviews:answer",
        "sessions:finalize",
        "analytics:view",
        "analytics:write",
        "audit:events:view",
        "billing:view",
        "billing:manage",
        "internal:email_queue:view",
        "internal:email_queue:process",
    },
    "member": {
        "organizations:list",
        "organizations:create",
        "organizations:members:list",
        "subjects:list",
        "subjects:create",
        "subjects:update",
        "tasks:list",
        "tasks:create",
        "tasks:update",
        "planner:generate",
        "reviews:list",
        "reviews:answer",
        "sessions:finalize",
        "analytics:view",
        "analytics:write",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict] = None,
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire, "jti": uuid.uuid4().hex, "type": token_type}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(
    subject: str,
    session_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta if expires_delta else timedelta(minutes=settings.refresh_token_expire_minutes),
        extra_claims={"sid": session_id},
    )


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        token_type = payload.get("type")
        if user_id is None:
            raise credentials_exception
        if token_type != "access":
            raise credentials_exception
        if jti and db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_organization_id: int | None = Header(default=None),
) -> Organization:
    memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
    if not memberships:
        raise HTTPException(status_code=403, detail="User has no organization membership")

    if x_organization_id is not None:
        selected = next((m for m in memberships if m.organization_id == x_organization_id), None)
        if not selected:
            raise HTTPException(status_code=403, detail="Organization access denied")
        organization = db.get(Organization, selected.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        return organization

    organization = db.get(Organization, memberships[0].organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


def get_current_membership(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> Membership:
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == current_user.id, Membership.organization_id == current_org.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Organization membership not found")
    return membership


def require_org_roles(*allowed_roles: str):
    normalized = {role.lower() for role in allowed_roles}

    def _checker(membership: Membership = Depends(get_current_membership)) -> Membership:
        if membership.role.lower() not in normalized:
            raise HTTPException(status_code=403, detail="Insufficient organization role")
        return membership

    return _checker


def require_permission(permission: str):
    def _checker(membership: Membership = Depends(get_current_membership)) -> Membership:
        role = membership.role.lower()
        allowed = ROLE_PERMISSIONS.get(role, set())
        if "*" in allowed or permission in allowed:
            return membership
        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")

    return _checker
