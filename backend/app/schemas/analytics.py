from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True
