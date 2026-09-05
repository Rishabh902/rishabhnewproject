from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow(): return datetime.now(timezone.utc)

class PartnerPreference(Base):
    __tablename__ = "partner_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    min_age: Mapped[int | None] = mapped_column(Integer)
    max_age: Mapped[int | None] = mapped_column(Integer)
    min_height_cm: Mapped[int | None] = mapped_column(Integer)
    max_height_cm: Mapped[int | None] = mapped_column(Integer)
    income: Mapped[str | None] = mapped_column(String(100))
    education: Mapped[str | None] = mapped_column(String(200))
    profession: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    community: Mapped[str | None] = mapped_column(String(120))
    other_criteria: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
