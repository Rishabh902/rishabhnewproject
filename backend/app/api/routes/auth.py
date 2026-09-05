from datetime import datetime, timezone, timedelta
from hashlib import sha256
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.api.deps import get_current_user

from app.core.rate_limit import limiter
from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token, create_registration_token,
    decode_token, hash_password, verify_otp_hash, verify_password,
)
from app.db.session import get_db
from app.models.otp import OTPCode
from app.models.profile import Profile
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, OTPLoginVerifyRequest, OTPRequest, OTPVerifyRequest,
    RegisterRequest, RegistrationProfileRequest, RegisterResponse,
    TokenResponse, UserResponse, ForgotPasswordRequest, ResetPasswordRequest,
)
from app.services.email import send_email
from app.services.otp import issue_otp
from app.services.profile import calculate_age

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def find_user(db: Session, contact: str):
    return db.query(User).filter(or_(User.phone == contact, User.email == contact)).first()

def tokens_for(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))

def validate_registration_token(token: str) -> int:
    try:
        payload = decode_token(token)
        if payload.get("type") != "registration":
            raise ValueError
        return int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Registration session expired. Please register again.")

@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(409, "Phone already registered")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(phone=data.phone, email=data.email, password_hash=hash_password(data.password),
                profile_for=data.profile_for.lower(), relationship=data.relationship,
                registration_location=data.registration_location, role="user", is_active=False)
    db.add(user); db.flush()
    db.add(Profile(user_id=user.id, status="DRAFT"))
    db.commit(); db.refresh(user)
    contact = user.phone
    otp = issue_otp(db, contact)
    return RegisterResponse(message="Account created. Complete the basic profile and verify OTP.",
                            user_id=user.id, otp_contact=contact,
                            registration_token=create_registration_token(user.id),
                            dev_otp=otp if settings.environment == "development" else None)

@router.post("/register/profile")
def create_registration_profile(data: RegistrationProfileRequest, db: Session = Depends(get_db)):
    user_id = validate_registration_token(data.registration_token)
    user = db.get(User, user_id)
    if not user or user.is_active:
        raise HTTPException(409, "Registration session is no longer available")
    if calculate_age(data.date_of_birth) < 18:
        raise HTTPException(422, "Profile owner must be at least 18 years old")
    profile = db.query(Profile).filter(Profile.user_id == user.id).first() or Profile(user_id=user.id)
    if not profile.id: db.add(profile)
    for key, value in data.model_dump(exclude={"registration_token"}).items():
        setattr(profile, key, value.strip() if isinstance(value, str) else value)
    profile.status = "DRAFT"
    db.commit(); db.refresh(profile)
    return {"message":"Basic profile saved. Verify OTP, then login and complete the full profile.","user_id":user.id,
            "otp_contact":user.phone, "profile_id":profile.id}

@router.post("/otp/request")
@limiter.limit("5/minute")
def request_otp(request: Request, data: OTPRequest, db: Session = Depends(get_db)):
    user = find_user(db, data.contact)
    if not user: raise HTTPException(404, "Account not found")
    if user.is_active: raise HTTPException(409, "Account is already verified")
    otp = issue_otp(db, data.contact)
    return {"message":"OTP sent", "dev_otp":otp if settings.environment=="development" else None}

@router.post("/otp/verify")
@limiter.limit("10/minute")
def verify_registration_otp(request: Request, data: OTPVerifyRequest, db: Session = Depends(get_db)):
    user_id = validate_registration_token(data.registration_token)
    user = db.get(User, user_id)
    if not user or user.phone != data.contact: raise HTTPException(401, "Invalid registration session")
    if user.is_active: raise HTTPException(409, "Account is already active")
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    required = ["name","gender","date_of_birth","caste","state","district","city_or_village","permanent_address","preferred_location"]
    if not profile or any(not getattr(profile, f, None) for f in required):
        raise HTTPException(422, "Complete the basic registration profile before verifying OTP")
    record = db.query(OTPCode).filter(OTPCode.contact==data.contact, OTPCode.verified==False).order_by(OTPCode.id.desc()).first()
    if not record: raise HTTPException(400, "OTP not found")
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc): raise HTTPException(400, "OTP expired")
    if record.attempts >= settings.otp_max_attempts: raise HTTPException(429, "Too many OTP attempts")
    record.attempts += 1
    if not verify_otp_hash(data.otp, record.code_hash):
        db.commit(); raise HTTPException(400, "Invalid OTP")
    record.verified=True; user.is_phone_verified=True; user.is_active=True
    db.commit()
    return {"message":"OTP verified. Account activated. Please login to complete your profile."}

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user=find_user(db,data.contact)
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Invalid credentials")
    if not user.is_active: raise HTTPException(403,"Verify registration OTP before login")
    return tokens_for(user)

@router.post("/login/otp/request")
@limiter.limit("5/minute")
def request_login_otp(request: Request, data: OTPRequest, db: Session = Depends(get_db)):
    user=find_user(db,data.contact)
    if not user: raise HTTPException(404,"Account not found")
    if not user.is_active: raise HTTPException(403,"Verify registration OTP before using OTP login")
    otp=issue_otp(db,data.contact)
    return {"message":"Login OTP sent","dev_otp":otp if settings.environment=="development" else None}

@router.post("/login/otp/verify", response_model=TokenResponse)
@limiter.limit("10/minute")
def verify_login_otp(request: Request,data:OTPLoginVerifyRequest,db:Session=Depends(get_db)):
    user=find_user(db,data.contact)
    if not user or not user.is_active: raise HTTPException(401,"Account not found or inactive")
    record=db.query(OTPCode).filter(OTPCode.contact==data.contact,OTPCode.verified==False).order_by(OTPCode.id.desc()).first()
    if not record: raise HTTPException(400,"OTP not found")
    expires_at=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc): raise HTTPException(400,"OTP expired")
    if record.attempts >= settings.otp_max_attempts: raise HTTPException(429,"Too many OTP attempts")
    record.attempts+=1
    if not verify_otp_hash(data.otp,record.code_hash): db.commit(); raise HTTPException(400,"Invalid OTP")
    record.verified=True; db.commit(); return tokens_for(user)

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Always return the same message to prevent account enumeration.
    user=db.query(User).filter(User.email==str(data.email).lower()).first()
    response={"message":"If an account exists for this email, a password reset link has been sent."}
    if not user:
        return response
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id==user.id, PasswordResetToken.used==False).update({"used":True})
    raw=secrets.token_urlsafe(48)
    token_hash=sha256(raw.encode()).hexdigest()
    expires=datetime.now(timezone.utc)+timedelta(minutes=settings.password_reset_expire_minutes)
    db.add(PasswordResetToken(user_id=user.id,token_hash=token_hash,expires_at=expires))
    db.commit()
    link=f"{settings.frontend_origin.rstrip('/')}/reset-password?token={raw}"
    html=f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
    <h2>Reset your password</h2><p>We received a request to create a new password.</p>
    <p><a href="{link}" style="padding:12px 20px;background:#7b1e3a;color:white;text-decoration:none;border-radius:6px">Create New Password</a></p>
    <p>This link expires in {settings.password_reset_expire_minutes} minutes and can be used once.</p>
    <p>If you did not request this, you can ignore this email.</p></div>"""
    try:
        send_email(str(user.email), "Reset your password", html)
    except Exception:
        # Do not expose SMTP configuration/errors to the client.
        db.rollback()
        raise HTTPException(503, "Password reset email could not be sent. Please try again later.")
    result=dict(response)
    if settings.environment=="development":
        result["dev_reset_url"]=link
    return result

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session=Depends(get_db)):
    token_hash=sha256(data.token.encode()).hexdigest()
    record=db.query(PasswordResetToken).filter(PasswordResetToken.token_hash==token_hash,PasswordResetToken.used==False).first()
    if not record: raise HTTPException(400,"Invalid or expired password reset link")
    expires=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc): record.used=True; db.commit(); raise HTTPException(400,"Password reset link has expired")
    user=db.get(User,record.user_id)
    if not user: raise HTTPException(400,"Invalid password reset request")
    user.password_hash=hash_password(data.password); record.used=True
    db.commit()
    return {"message":"Password changed successfully. You can now login with your new password."}

@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str, db: Session=Depends(get_db)):
    try:
        payload=decode_token(refresh_token)
        if payload.get("type")!="refresh": raise ValueError
        user_id=int(payload["sub"])
    except Exception: raise HTTPException(401,"Invalid or expired refresh token")
    user=db.get(User,user_id)
    if not user or not user.is_active: raise HTTPException(401,"User is not active")
    return tokens_for(user)

@router.post("/logout")
def logout(): return {"message":"Logout acknowledged. Client must remove local tokens."}

@router.get("/me", response_model=UserResponse)
def me(user: User=Depends(get_current_user)): return user
