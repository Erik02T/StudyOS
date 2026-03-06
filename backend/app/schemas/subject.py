from pydantic import BaseModel, Field


class SubjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    importance_level: int = Field(default=3, ge=1, le=5)
    difficulty: int = Field(default=3, ge=1, le=5)
    category: str = Field(default="general", max_length=50)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    importance_level: int | None = Field(default=None, ge=1, le=5)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    category: str | None = Field(default=None, max_length=50)


class SubjectOut(SubjectBase):
    id: int

    class Config:
        from_attributes = True

