from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class BillingMetricUsage(BaseModel):
    metric: str
    used: int
    limit: int
    remaining: int


class BillingSubscriptionResponse(BaseModel):
    organization_id: int
    plan: str
    status: str
    current_period_start: dt.date
    current_period_end: dt.date
    usage: list[BillingMetricUsage]
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None


class BillingPlanUpdateRequest(BaseModel):
    plan: str = Field(pattern="^(free|pro)$")


class BillingCheckoutSessionRequest(BaseModel):
    plan: str = Field(default="pro", pattern="^(pro)$")
    success_url: str = Field(min_length=5, max_length=500)
    cancel_url: str = Field(min_length=5, max_length=500)


class BillingCheckoutSessionResponse(BaseModel):
    checkout_url: str
    provider: str = "stripe"
