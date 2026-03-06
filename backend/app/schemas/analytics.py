from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class PerformanceLogRequest(BaseModel):
    date: dt.date | None = None
    completed_tasks: int = Field(default=0, ge=0, le=200)
    study_minutes: int = Field(default=0, ge=0, le=1440)
    focus_score: float = Field(default=0.0, ge=0, le=100)
    productivity_index: float | None = Field(default=None, ge=0, le=100)
    time_block: str | None = Field(default=None, max_length=32)
    accumulate: bool = False


class PerformanceLogResponse(BaseModel):
    id: int
    date: dt.date
    completed_tasks: int
    study_minutes: int
    focus_score: float
    productivity_index: float
    time_block: str

    model_config = ConfigDict(from_attributes=True)


class StudyEventOut(BaseModel):
    id: int
    organization_id: int
    user_id: int | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    payload: dict | None
    created_at: dt.datetime


class StudyEventListResponse(BaseModel):
    items: list[StudyEventOut]
    total: int
    page: int
    page_size: int
    pages: int
