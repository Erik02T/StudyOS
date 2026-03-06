import datetime as dt

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    available_hours_per_day: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    preferred_time_block: Mapped[str] = mapped_column(String(32), default="19:00-21:00", nullable=False)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
