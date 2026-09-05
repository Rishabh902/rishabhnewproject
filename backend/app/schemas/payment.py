from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlanResponse(BaseModel):
    code: str
    name: str
    price_inr: float
    duration_days: int
    max_match_score: int
    features: list[str]


class InitiatePaymentRequest(BaseModel):
    plan_code: str | None = Field(
        default=None,
        max_length=40,
    )

    coupon_code: str | None = Field(
        default=None,
        max_length=50,
    )

    match_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    plan_code: str

    amount_inr: float

    discount_inr: float

    final_amount_inr: float

    upi_vpa: str

    transaction_note: str

    transaction_ref: str

    utr_reference: str | None

    status: str

    rejection_reason: str | None = None

    created_at: datetime

    upi_uri: str


class SubmitUtrRequest(BaseModel):
    utr_reference: str = Field(
        min_length=4,
        max_length=60,
    )


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    plan_code: str

    start_date: datetime

    end_date: datetime

    is_active: bool


class RejectPaymentRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=500,
    )


class CouponValidateRequest(BaseModel):
    plan_code: str = Field(
        min_length=1,
        max_length=40,
    )

    coupon_code: str = Field(
        min_length=1,
        max_length=50,
    )


class CouponValidateResponse(BaseModel):
    valid: bool
    coupon_code: str
    original_amount: float
    discount_amount: float
    final_amount: float
    message: str


class CouponCreateRequest(BaseModel):
    code: str = Field(
        min_length=3,
        max_length=50,
    )

    discount_type: str = Field(
        min_length=4,
        max_length=20,
    )

    discount_value: float = Field(
        gt=0,
    )

    max_uses: int | None = Field(
        default=None,
        gt=0,
    )

    valid_from: datetime | None = None

    valid_until: datetime | None = None


class CouponResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    code: str

    discount_type: str

    discount_value: float

    max_uses: int | None

    used_count: int

    valid_from: datetime | None

    valid_until: datetime | None

    is_active: bool 
