from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow(): return datetime.now(timezone.utc)

class Verification(Base):
    __tablename__ = "verifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    parent_mobile: Mapped[str | None] = mapped_column(String(20))
    parent_status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED", nullable=False)
    identity_status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED", nullable=False)
    identity_reference: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
