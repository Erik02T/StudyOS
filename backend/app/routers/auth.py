import datetime as dt
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.action_token import ActionToken
from app.models.auth_session import AuthSession
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LogoutRequest, RefreshTokenRequest, TokenResponse, UserLogin, UserRegister
from app.schemas.auth import (
    ActionRequestResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    VerifyEmailRequest,
)
from app.services.email_queue_service import EmailQueueService
from app.services.email_templates import EmailTemplates
from app.services.rate_limit_service import RateLimitService

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_identifier(request: Request, email: str | None = None) -> str:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip = ip or (request.client.host if request.client else "unknown")
    return f"{ip}:{email.lower()}" if email else ip


def _issue_token_pair(db: Session, user: User) -> TokenResponse:
    session_id = uuid.uuid4().hex
    refresh_token = create_refresh_token(subject=str(user.id), session_id=session_id)
    refresh_payload = decode_token(refresh_token)
    expires_at = dt.datetime.utcfromtimestamp(refresh_payload["exp"])

    auth_session = AuthSession(
        session_id=session_id,
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        created_at=dt.datetime.utcnow(),
        expires_at=expires_at,
        revoked_at=None,
    )
    db.add(auth_session)
    db.commit()
    return TokenResponse(access_token=create_access_token(subject=str(user.id)), refresh_token=refresh_token)


def _issue_action_token(
    db: Session,
    user: User,
    purpose: str,
    expire_minutes: int,
) -> str:
    raw_token = secrets.token_urlsafe(32)
    token = ActionToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=hash_token(raw_token),
        created_at=dt.datetime.utcnow(),
        expires_at=dt.datetime.utcnow() + dt.timedelta(minutes=expire_minutes),
        used_at=None,
    )
    db.add(token)
    db.commit()
    return raw_token


def _consume_action_token(db: Session, raw_token: str, purpose: str) -> ActionToken:
    token_hash = hash_token(raw_token)
    token = (
        db.query(ActionToken)
        .filter(ActionToken.token_hash == token_hash, ActionToken.purpose == purpose, ActionToken.used_at.is_(None))
        .first()
    )
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or already used token")
    if token.expires_at < dt.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
    token.used_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(token)
    return token


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request, payload.email),
        endpoint="auth:register",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        available_hours_per_day=payload.available_hours_per_day,
        preferred_time_block=payload.preferred_time_block,
    )
    db.add(user)
    db.flush()

    base_slug = payload.email.split("@")[0].strip().lower().replace(" ", "-")
    slug = base_slug or f"user-{user.id}"
    candidate = slug
    seq = 1
    while db.query(Organization).filter(Organization.slug == candidate).first():
        seq += 1
        candidate = f"{slug}-{seq}"

    organization = Organization(name=f"{payload.email}'s Workspace", slug=candidate)
    db.add(organization)
    db.flush()

    membership = Membership(user_id=user.id, organization_id=organization.id, role="owner")
    db.add(membership)

    db.commit()
    db.refresh(user)

    return _issue_token_pair(db=db, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request, payload.email),
        endpoint="auth:login",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _issue_token_pair(db=db, user=user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request),
        endpoint="auth:refresh",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )
    try:
        token_payload = decode_token(payload.refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = token_payload.get("sub")
    session_id = token_payload.get("sid")
    if not user_id or not session_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    auth_session = (
        db.query(AuthSession).filter(AuthSession.session_id == session_id, AuthSession.user_id == int(user_id)).first()
    )
    if not auth_session:
        raise HTTPException(status_code=401, detail="Session not found")
    if auth_session.revoked_at is not None or auth_session.expires_at < dt.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session revoked or expired")
    if auth_session.refresh_token_hash != hash_token(payload.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token mismatch")

    auth_session.revoked_at = dt.datetime.utcnow()
    db.commit()

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _issue_token_pair(db=db, user=user)


@router.post("/logout")
def logout(
    request: Request,
    payload: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request, current_user.email),
        endpoint="auth:logout",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )

    auth_header = request.headers.get("authorization", "")
    access_token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else None
    if access_token:
        try:
            payload_token = decode_token(access_token)
            jti = payload_token.get("jti")
            exp = payload_token.get("exp")
            if jti and exp:
                db.add(
                    RevokedToken(
                        jti=jti,
                        token_type="access",
                        expires_at=dt.datetime.utcfromtimestamp(exp),
                        revoked_at=dt.datetime.utcnow(),
                    )
                )
                db.commit()
        except JWTError:
            pass

    if payload and payload.revoke_all_sessions:
        db.query(AuthSession).filter(
            AuthSession.user_id == current_user.id, AuthSession.revoked_at.is_(None)
        ).update({"revoked_at": dt.datetime.utcnow()})
        db.commit()
        return {"message": "Logged out from all sessions"}

    if payload and payload.refresh_token:
        try:
            refresh_payload = decode_token(payload.refresh_token)
            sid = refresh_payload.get("sid")
            if sid:
                session = (
                    db.query(AuthSession)
                    .filter(
                        AuthSession.session_id == sid,
                        AuthSession.user_id == current_user.id,
                        AuthSession.revoked_at.is_(None),
                    )
                    .first()
                )
                if session:
                    session.revoked_at = dt.datetime.utcnow()
                    db.commit()
        except JWTError:
            pass

    return {"message": "Logged out"}


@router.post("/request-email-verification", response_model=ActionRequestResponse)
def request_email_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActionRequestResponse:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request, current_user.email),
        endpoint="auth:request-email-verification",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )
    raw_token = _issue_action_token(
        db=db,
        user=current_user,
        purpose="verify_email",
        expire_minutes=settings.email_verification_token_expire_minutes,
    )
    subject, text_body, html_body = EmailTemplates.verify_email(current_user.email, raw_token)
    EmailQueueService.enqueue(
        db=db,
        to_email=current_user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    return ActionRequestResponse(
        message="If your account exists, a verification token has been issued.",
        action_token=raw_token if settings.action_token_expose_in_response else None,
    )


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict:
    token = _consume_action_token(db=db, raw_token=payload.token, purpose="verify_email")
    user = db.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_email_verified = True
    user.email_verified_at = dt.datetime.utcnow()
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/request-password-reset", response_model=ActionRequestResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ActionRequestResponse:
    settings = get_settings()
    RateLimitService.hit(
        db=db,
        identifier=_client_identifier(request, payload.email),
        endpoint="auth:request-password-reset",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
    )
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return ActionRequestResponse(message="If your account exists, a reset token has been issued.")
    raw_token = _issue_action_token(
        db=db,
        user=user,
        purpose="reset_password",
        expire_minutes=settings.password_reset_token_expire_minutes,
    )
    subject, text_body, html_body = EmailTemplates.password_reset(user.email, raw_token)
    EmailQueueService.enqueue(
        db=db,
        to_email=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    return ActionRequestResponse(
        message="If your account exists, a reset token has been issued.",
        action_token=raw_token if settings.action_token_expose_in_response else None,
    )


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)) -> dict:
    token = _consume_action_token(db=db, raw_token=payload.token, purpose="reset_password")
    user = db.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(payload.new_password)
    db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).update(
        {"revoked_at": dt.datetime.utcnow()}
    )
    db.commit()
    return {"message": "Password updated successfully"}
