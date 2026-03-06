from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    estimated_time: int = Field(default=30, ge=5, le=240)
    mastery_level: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="pending", max_length=30)


class TaskCreate(TaskBase):
    subject_id: int


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    estimated_time: int | None = Field(default=None, ge=5, le=240)
    mastery_level: int | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, max_length=30)


class TaskOut(TaskBase):
    id: int
    subject_id: int

    class Config:
        from_attributes = True
