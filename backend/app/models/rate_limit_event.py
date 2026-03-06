import datetime as dt

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)

