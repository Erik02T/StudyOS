from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    available_minutes: int | None = Field(default=None, ge=30, le=960)
    time_block: str | None = Field(default=None, max_length=32)

