from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class ReviewDueItem(BaseModel):
    task_id: int
    title: str
    subject: str
    category: str
    estimated_time: int
    next_review_date: dt.date
    interval: int
    ease_factor: float
    mastery_level: int


class ReviewAnswerRequest(BaseModel):
    task_id: int
    quality: int = Field(ge=0, le=5)
    review_date: dt.date | None = None


class ReviewAnswerResponse(BaseModel):
    task_id: int
    quality: int
    previous_interval: int
    new_interval: int
    previous_ease_factor: float
    new_ease_factor: float
    previous_mastery_level: int
    new_mastery_level: int
    next_review_date: dt.date
