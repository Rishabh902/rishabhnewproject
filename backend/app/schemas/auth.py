from datetime import date
from pydantic import BaseModel, EmailStr, Field, model_validator

class RegisterRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    profile_for: str = Field(min_length=2, max_length=40)
    relationship: str | None = Field(default=None, max_length=80)
    registration_location: str = Field(min_length=2, max_length=200)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        if self.profile_for.lower() != "self" and not self.relationship:
            raise ValueError("Relationship is required when creating a profile for someone else")
        return self

class RegistrationProfileRequest(BaseModel):
    registration_token: str = Field(min_length=20)
    name: str = Field(min_length=2, max_length=120)
    gender: str = Field(min_length=2, max_length=30)
    date_of_birth: date
    caste: str = Field(min_length=2, max_length=150)
    state: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=120)
    city_or_village: str = Field(min_length=2, max_length=150)
    permanent_address: str = Field(min_length=5)
    preferred_location: str = Field(min_length=2, max_length=200)

class RegisterResponse(BaseModel):
    message: str
    user_id: int
    otp_contact: str
    registration_token: str
    dev_otp: str | None = None

class OTPRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=255)
class OTPVerifyRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=255)
    otp: str = Field(pattern=r"^\d{6}$")
    registration_token: str = Field(min_length=20)
class OTPLoginVerifyRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=255)
    otp: str = Field(pattern=r"^\d{6}$")
class LoginRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        return self
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
class UserResponse(BaseModel):
    id: int
    phone: str | None
    email: EmailStr | None
    profile_for: str
    relationship: str | None
    registration_location: str | None
    role: str
    is_active: bool
    is_phone_verified: bool
    is_email_verified: bool
    model_config = {"from_attributes": True}
