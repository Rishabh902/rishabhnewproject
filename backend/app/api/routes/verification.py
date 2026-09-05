from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.otp import OTPCode
from app.models.user import User
from app.models.verification import Verification
from app.schemas.profile import ParentVerificationRequest, ParentVerificationVerify, IdentityVerificationRequest, IdentityVerificationVerify, VerificationResponse
from app.services.otp import issue_otp
from app.core.security import verify_otp_hash
from datetime import datetime, timezone

router = APIRouter(prefix="/api/verification", tags=["Verification"])

def get_ver(db, user_id):
    item = db.query(Verification).filter(Verification.user_id == user_id).first()
    if not item:
        item = Verification(user_id=user_id); db.add(item); db.commit(); db.refresh(item)
    return item

@router.get("/status", response_model=VerificationResponse)
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_ver(db, user.id)

@router.post("/parent/request")
def parent_request(data: ParentVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.parent_mobile == user.phone: raise HTTPException(422, "Parent mobile must be different from user's mobile")
    v = get_ver(db, user.id); v.parent_mobile = data.parent_mobile; v.parent_status = "OTP_SENT"; db.commit()
    otp = issue_otp(db, data.parent_mobile)
    return {"message": "Parent verification OTP sent", "dev_otp": otp if settings.environment == "development" else None}

@router.post("/parent/verify")
def parent_verify(data: ParentVerificationVerify, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_ver(db, user.id)
    if not v.parent_mobile: raise HTTPException(400, "Request parent verification first")
    record = db.query(OTPCode).filter(OTPCode.contact == v.parent_mobile, OTPCode.verified == False).order_by(OTPCode.id.desc()).first()
    if not record: raise HTTPException(400, "OTP expired or not found")
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc): raise HTTPException(400, "OTP expired or not found")
    if record.attempts >= settings.otp_max_attempts: raise HTTPException(429, "Too many attempts")
    record.attempts += 1
    if not verify_otp_hash(data.otp, record.code_hash): db.commit(); raise HTTPException(400, "Invalid OTP")
    record.verified = True; v.parent_status = "VERIFIED"; db.commit()
    return {"message": "Parent mobile verified"}

@router.post("/identity/request")
def identity_request(data: IdentityVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_ver(db, user.id); v.identity_reference = data.reference; v.identity_status = "PENDING"; db.commit()
    return {"message": "Identity verification submitted for verification"}

@router.post("/identity/verify")
def identity_verify(data: IdentityVerificationVerify, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_ver(db, user.id)
    if v.identity_status != "PENDING": raise HTTPException(400, "No pending identity verification")
    v.identity_status = "VERIFIED" if data.approved else "REJECTED"; db.commit()
    return {"message": f"Identity verification {v.identity_status.lower()}"}
