from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class SessionFinalizeRequest(BaseModel):
    date: dt.date | None = None
    source: str = Field(default="manual", max_length=24)
    study_minutes: int = Field(default=0, ge=0, le=1440)
    completed_tasks: int | None = Field(default=None, ge=0, le=200)
    focus_score: float | None = Field(default=None, ge=0, le=100)
    productivity_index: float | None = Field(default=None, ge=0, le=100)
    time_block: str | None = Field(default=None, max_length=32)
    quality: int | None = Field(default=None, ge=0, le=5)


class SessionFinalizeResponse(BaseModel):
    message: str
    source: str
    performance_id: int
    date: dt.date
    completed_tasks: int
    study_minutes: int
    focus_score: float
    productivity_index: float
    time_block: str
