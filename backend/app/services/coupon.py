from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.payment import Coupon, CouponUsage

CENT = Decimal("0.01")


def normalize_code(code: str) -> str:
    return code.strip().upper()


def calculate_discount(db: Session, user_id: int, plan_code: str, amount: Decimal, code: str | None) -> tuple[Coupon | None, Decimal]:
    if not code:
        return None, Decimal("0.00")

    now = datetime.now(timezone.utc)
    coupon = (
        db.query(Coupon)
        .filter(func.upper(Coupon.code) == normalize_code(code), Coupon.is_active == True)
        .first()
    )
    if not coupon:
        raise HTTPException(400, "Invalid or inactive coupon")

    start = coupon.valid_from if coupon.valid_from.tzinfo else coupon.valid_from.replace(tzinfo=timezone.utc)
    end = coupon.valid_until if coupon.valid_until.tzinfo else coupon.valid_until.replace(tzinfo=timezone.utc)
    if now < start or now > end:
        raise HTTPException(400, "Coupon is outside its validity period")
    if coupon.applicable_plan_code and coupon.applicable_plan_code.upper() != plan_code.upper():
        raise HTTPException(400, "Coupon is not valid for this plan")
    if coupon.min_order_amount_inr is not None and amount < coupon.min_order_amount_inr:
        raise HTTPException(400, "Minimum order amount for this coupon is not met")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(400, "Coupon usage limit has been reached")

    user_usage = db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id, CouponUsage.user_id == user_id).count()
    if user_usage >= coupon.per_user_limit:
        raise HTTPException(400, "You have already used this coupon the maximum allowed times")

    if coupon.discount_type == "PERCENTAGE":
        discount = (amount * coupon.discount_value / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
    elif coupon.discount_type == "FIXED":
        discount = coupon.discount_value.quantize(CENT)
    else:
        raise HTTPException(500, "Coupon configuration is invalid")

    if coupon.max_discount_inr is not None:
        discount = min(discount, coupon.max_discount_inr)
    discount = min(discount, amount)
    return coupon, discount.quantize(CENT)
