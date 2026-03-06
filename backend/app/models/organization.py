from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="organization", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="organization", cascade="all, delete-orphan")

