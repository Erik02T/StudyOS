from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    importance_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)

    user = relationship("User", back_populates="subjects")
    organization = relationship("Organization", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete-orphan")
