from __future__ import annotations

import datetime as dt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.organization_subscription import OrganizationSubscription
from app.models.organization_usage import OrganizationUsage
from app.models.subject import Subject


class BillingService:
    METRIC_TASKS_CREATED = "tasks_created_monthly"
    METRIC_REVIEWS_ANSWERED = "reviews_answered_monthly"
    METRIC_SESSIONS_FINALIZED = "sessions_finalized_monthly"

    @staticmethod
    def _period_start(day: dt.date | None = None) -> dt.date:
        current = day or dt.date.today()
        return current.replace(day=1)

    @staticmethod
    def _period_end(start: dt.date) -> dt.date:
        if start.month == 12:
            next_month = dt.date(start.year + 1, 1, 1)
        else:
            next_month = dt.date(start.year, start.month + 1, 1)
        return next_month - dt.timedelta(days=1)

    @staticmethod
    def get_or_create_subscription(db: Session, organization_id: int) -> OrganizationSubscription:
        row = (
            db.query(OrganizationSubscription)
            .filter(OrganizationSubscription.organization_id == organization_id)
            .first()
        )
        if row:
            return row

        row = OrganizationSubscription(organization_id=organization_id, plan="free", status="active")
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def plan_limits(plan: str) -> dict[str, int]:
        settings = get_settings()
        normalized = (plan or "free").lower()
        if normalized == "pro":
            return {
                "max_subjects": settings.billing_pro_max_subjects,
                BillingService.METRIC_TASKS_CREATED: settings.billing_pro_tasks_per_month,
                BillingService.METRIC_REVIEWS_ANSWERED: settings.billing_pro_reviews_per_month,
                BillingService.METRIC_SESSIONS_FINALIZED: settings.billing_pro_sessions_per_month,
            }
        return {
            "max_subjects": settings.billing_free_max_subjects,
            BillingService.METRIC_TASKS_CREATED: settings.billing_free_tasks_per_month,
            BillingService.METRIC_REVIEWS_ANSWERED: settings.billing_free_reviews_per_month,
            BillingService.METRIC_SESSIONS_FINALIZED: settings.billing_free_sessions_per_month,
        }

    @staticmethod
    def assert_subject_capacity(db: Session, organization_id: int) -> None:
        subscription = BillingService.get_or_create_subscription(db, organization_id)
        limits = BillingService.plan_limits(subscription.plan)
        max_subjects = limits["max_subjects"]

        current_count = (
            db.query(Subject)
            .filter(Subject.organization_id == organization_id)
            .count()
        )
        if current_count >= max_subjects:
            raise HTTPException(
                status_code=402,
                detail=f"Plan limit reached: max {max_subjects} subjects for plan '{subscription.plan}'",
            )

    @staticmethod
    def _get_or_create_usage_row(
        db: Session,
        *,
        organization_id: int,
        metric: str,
        period_start: dt.date,
    ) -> OrganizationUsage:
        row = (
            db.query(OrganizationUsage)
            .filter(
                OrganizationUsage.organization_id == organization_id,
                OrganizationUsage.period_start == period_start,
                OrganizationUsage.metric == metric,
            )
            .first()
        )
        if row:
            return row
        row = OrganizationUsage(
            organization_id=organization_id,
            period_start=period_start,
            metric=metric,
            used=0,
        )
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def check_and_consume(db: Session, *, organization_id: int, metric: str, amount: int = 1) -> None:
        if amount <= 0:
            return
        subscription = BillingService.get_or_create_subscription(db, organization_id)
        limits = BillingService.plan_limits(subscription.plan)
        limit_value = limits.get(metric)
        if limit_value is None:
            return

        period_start = BillingService._period_start()
        usage = BillingService._get_or_create_usage_row(
            db=db, organization_id=organization_id, metric=metric, period_start=period_start
        )
        next_used = usage.used + amount
        if next_used > limit_value:
            raise HTTPException(
                status_code=402,
                detail=f"Plan limit reached for metric '{metric}'. Upgrade required.",
            )
        usage.used = next_used
        db.commit()

    @staticmethod
    def usage_snapshot(db: Session, organization_id: int) -> dict:
        subscription = BillingService.get_or_create_subscription(db, organization_id)
        limits = BillingService.plan_limits(subscription.plan)
        period_start = BillingService._period_start()
        period_end = BillingService._period_end(period_start)

        metrics = [
            BillingService.METRIC_TASKS_CREATED,
            BillingService.METRIC_REVIEWS_ANSWERED,
            BillingService.METRIC_SESSIONS_FINALIZED,
        ]
        usage_rows = (
            db.query(OrganizationUsage)
            .filter(
                OrganizationUsage.organization_id == organization_id,
                OrganizationUsage.period_start == period_start,
                OrganizationUsage.metric.in_(metrics),
            )
            .all()
        )
        usage_map = {row.metric: row.used for row in usage_rows}
        usage = []
        for metric in metrics:
            limit_value = limits.get(metric, 0)
            used = usage_map.get(metric, 0)
            usage.append(
                {
                    "metric": metric,
                    "used": used,
                    "limit": limit_value,
                    "remaining": max(limit_value - used, 0),
                }
            )

        return {
            "organization_id": organization_id,
            "plan": subscription.plan,
            "status": subscription.status,
            "current_period_start": period_start,
            "current_period_end": period_end,
            "usage": usage,
            "stripe_customer_id": subscription.stripe_customer_id,
            "stripe_subscription_id": subscription.stripe_subscription_id,
        }
