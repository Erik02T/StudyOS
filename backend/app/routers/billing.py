from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    get_current_membership,
    get_current_organization,
    get_current_user,
    require_permission,
)
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.organization_subscription import OrganizationSubscription
from app.models.user import User
from app.schemas.billing import (
    BillingCheckoutSessionRequest,
    BillingCheckoutSessionResponse,
    BillingPlanUpdateRequest,
    BillingSubscriptionResponse,
)
from app.services.billing_service import BillingService
from app.services.stripe_billing_service import StripeBillingService
from app.services.study_event_service import StudyEventService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=BillingSubscriptionResponse)
def get_subscription(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _perm=Depends(require_permission("billing:view")),
) -> BillingSubscriptionResponse:
    return BillingService.usage_snapshot(db=db, organization_id=current_org.id)


@router.patch("/subscription", response_model=BillingSubscriptionResponse)
def update_subscription_plan(
    payload: BillingPlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    membership: Membership = Depends(get_current_membership),
    _perm=Depends(require_permission("billing:manage")),
) -> BillingSubscriptionResponse:
    settings = get_settings()
    if not settings.billing_allow_manual_plan_change:
        raise HTTPException(status_code=403, detail="Manual plan change is disabled")
    if membership.role.lower() != "owner":
        raise HTTPException(status_code=403, detail="Only organization owner can change plan")

    subscription = BillingService.get_or_create_subscription(db, current_org.id)
    subscription.plan = payload.plan
    subscription.status = "active"
    db.commit()

    StudyEventService.record(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        event_type="billing.plan_changed",
        entity_type="subscription",
        entity_id=str(subscription.id),
        payload={"plan": payload.plan},
        commit=True,
    )
    return BillingService.usage_snapshot(db=db, organization_id=current_org.id)


@router.post("/checkout-session", response_model=BillingCheckoutSessionResponse)
def create_checkout_session(
    payload: BillingCheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    membership: Membership = Depends(get_current_membership),
    _perm=Depends(require_permission("billing:manage")),
) -> BillingCheckoutSessionResponse:
    if membership.role.lower() != "owner":
        raise HTTPException(status_code=403, detail="Only organization owner can create checkout session")

    result = StripeBillingService.create_checkout_session(
        db=db,
        organization_id=current_org.id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    StudyEventService.record(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        event_type="billing.checkout_session.created",
        entity_type="organization",
        entity_id=str(current_org.id),
        payload={"provider": "stripe", "plan": payload.plan},
        commit=True,
    )
    return BillingCheckoutSessionResponse(**result)


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        import stripe  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise HTTPException(status_code=503, detail="Stripe SDK is not installed") from exc

    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()

    if settings.stripe_webhook_secret:
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        try:
            event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature") from exc
    else:
        # Fallback for staging/dev when signature secret is not set.
        import json

        try:
            event = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    event_type = event.get("type")
    data_object = (event.get("data") or {}).get("object") or {}
    metadata = data_object.get("metadata") or {}
    organization_id = metadata.get("organization_id")

    if organization_id and event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        subscription = BillingService.get_or_create_subscription(db, int(organization_id))
        subscription.plan = "pro"
        subscription.status = data_object.get("status") or "active"
        subscription.stripe_customer_id = data_object.get("customer")
        subscription.stripe_subscription_id = data_object.get("id")
        db.commit()

    if organization_id and event_type in {"customer.subscription.deleted"}:
        subscription = BillingService.get_or_create_subscription(db, int(organization_id))
        subscription.plan = "free"
        subscription.status = "canceled"
        db.commit()

    if organization_id:
        StudyEventService.record(
            db=db,
            organization_id=int(organization_id),
            user_id=None,
            event_type=f"billing.webhook.{event_type}",
            entity_type="organization",
            entity_id=str(organization_id),
            payload={"provider": "stripe"},
            commit=True,
        )

    return {"received": True}
