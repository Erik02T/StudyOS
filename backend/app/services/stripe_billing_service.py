from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.organization_subscription import OrganizationSubscription


class StripeBillingService:
    @staticmethod
    def _get_stripe_module():
        try:
            import stripe  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on optional package
            raise HTTPException(status_code=503, detail="Stripe SDK is not installed") from exc
        return stripe

    @staticmethod
    def create_checkout_session(
        db: Session,
        *,
        organization_id: int,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        settings = get_settings()
        if not settings.billing.stripe_secret_key or not settings.billing.stripe_price_pro_monthly:
            raise HTTPException(status_code=503, detail="Stripe is not configured")

        stripe = StripeBillingService._get_stripe_module()
        stripe.api_key = settings.billing.stripe_secret_key

        subscription = (
            db.query(OrganizationSubscription)
            .filter(OrganizationSubscription.organization_id == organization_id)
            .first()
        )
        customer = subscription.stripe_customer_id if subscription else None

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer,
            line_items=[{"price": settings.billing.stripe_price_pro_monthly, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"organization_id": str(organization_id), "target_plan": "pro"},
        )
        return {"checkout_url": session.url, "provider": "stripe"}
