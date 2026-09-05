from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Records every admin action that changes another user's state --
    profile approval/rejection and payment verification/rejection, per the
    documented requirement to audit approval, rejection, ban and payment
    actions. Append-only: never updated or deleted by the app."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


def record_audit(db, admin_user_id: int, action: str, target_user_id: int | None = None, detail: str | None = None) -> None:
    """Write an audit row. Caller is still responsible for db.commit()."""
    db.add(AuditLog(admin_user_id=admin_user_id, action=action, target_user_id=target_user_id, detail=detail))
