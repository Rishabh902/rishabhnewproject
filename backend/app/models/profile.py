from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow(): return datetime.now(timezone.utc)

class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120))
    gender: Mapped[str | None] = mapped_column(String(30))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    caste: Mapped[str | None] = mapped_column(String(150))
    community: Mapped[str | None] = mapped_column(String(150))
    gothra: Mapped[str | None] = mapped_column(String(120))
    education: Mapped[str | None] = mapped_column(String(200))
    degree: Mapped[str | None] = mapped_column(String(200))
    profession: Mapped[str | None] = mapped_column(String(200))
    income: Mapped[str | None] = mapped_column(String(100))
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(120))
    city_or_village: Mapped[str | None] = mapped_column(String(150))
    permanent_address: Mapped[str | None] = mapped_column(Text)
    preferred_location: Mapped[str | None] = mapped_column(String(200))
    family_details: Mapped[str | None] = mapped_column(Text)
    photo_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
