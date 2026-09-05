from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InterestCreate(BaseModel):
    receiver_id: int = Field(gt=0)


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    other_user_name: str | None = None
    other_user_photo_url: str | None = None


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_one_id: int
    user_two_id: int
    score: int | None
    source: str
    created_at: datetime
    other_user_id: int
    other_user_name: str | None = None
    other_user_photo_url: str | None = None


class ShortlistCreate(BaseModel):
    profile_user_id: int = Field(gt=0)


class ShortlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    profile_user_id: int
    created_at: datetime
    profile_name: str | None = None
    profile_photo_url: str | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recipient_id: int
    type: str
    title: str
    message: str
    payload: dict | None
    is_read: bool
    created_at: datetime
