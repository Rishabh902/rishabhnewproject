from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class ProfileUpsert(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    gender: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    caste: str | None = Field(default=None, max_length=150)
    community: str | None = Field(default=None, max_length=150)
    gothra: str | None = Field(default=None, max_length=120)
    education: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=200)
    profession: str | None = Field(default=None, max_length=200)
    income: str | None = Field(default=None, max_length=100)
    height_cm: int | None = Field(default=None, ge=80, le=250)
    weight_kg: int | None = Field(default=None, ge=20, le=250)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=120)
    city_or_village: str | None = Field(default=None, max_length=150)
    permanent_address: str | None = None
    preferred_location: str | None = Field(default=None, max_length=200)
    family_details: str | None = None

class ProfileResponse(ProfileUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    status: str
    rejection_reason: str | None = None
    photo_url: str | None = None
    photo_count: int = 0
    minimum_photos_required: int = 10

class PreferenceUpsert(BaseModel):
    min_age: int | None = Field(default=None, ge=18, le=100)
    max_age: int | None = Field(default=None, ge=18, le=100)
    min_height_cm: int | None = Field(default=None, ge=80, le=250)
    max_height_cm: int | None = Field(default=None, ge=80, le=250)
    income: str | None = Field(default=None, max_length=100)
    education: str | None = Field(default=None, max_length=200)
    profession: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    community: str | None = Field(default=None, max_length=120)
    other_criteria: str | None = None

class PreferenceResponse(PreferenceUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class MatchProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    gender: str | None
    date_of_birth: date | None
    caste: str | None = None
    community: str | None
    education: str | None
    degree: str | None = None
    profession: str | None
    income: str | None
    height_cm: int | None
    weight_kg: int | None = None
    state: str | None = None
    district: str | None = None
    city_or_village: str | None = None
    preferred_location: str | None
    photo_url: str | None
    status: str
    compatibility_score: int
    match_breakdown: dict[str, int] = Field(default_factory=dict)
    relaxed_match: bool = False

class ParentVerificationRequest(BaseModel):
    parent_mobile: str = Field(min_length=10, max_length=20)
class ParentVerificationVerify(BaseModel):
    otp: str = Field(min_length=4, max_length=8)
class IdentityVerificationRequest(BaseModel):
    reference: str = Field(min_length=3, max_length=120)
class IdentityVerificationVerify(BaseModel):
    approved: bool
class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    parent_mobile: str | None
    parent_status: str
    identity_status: str
    identity_reference: str | None
