import datetime as dt

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    study_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_block: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    focus_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    productivity_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user = relationship("User", back_populates="performances")
    organization = relationship("Organization", back_populates="performances")
