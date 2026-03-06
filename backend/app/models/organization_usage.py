import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrganizationUsage(Base):
    __tablename__ = "organization_usage"
    __table_args__ = (
        UniqueConstraint("organization_id", "period_start", "metric", name="uq_org_usage_period_metric"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    period_start: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False
    )
