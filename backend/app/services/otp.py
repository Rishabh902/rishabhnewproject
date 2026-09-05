from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import generate_otp, hash_otp
from app.models.otp import OTPCode

def issue_otp(db: Session, contact: str) -> str:
    db.execute(delete(OTPCode).where(OTPCode.contact == contact, OTPCode.verified == False))
    otp = generate_otp()
    record = OTPCode(
        contact=contact,
        code_hash=hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes),
    )
    db.add(record)
    db.commit()
    return otp
