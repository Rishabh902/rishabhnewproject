from datetime import datetime, timedelta, timezone
from secrets import token_hex

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.payment import (
    Coupon,
    CouponUsage,
    PaymentOrder,
    Subscription,
)
from app.models.user import User
from app.schemas.payment import (
    CouponValidateRequest,
    CouponValidateResponse,
    InitiatePaymentRequest,
    PaymentOrderResponse,
    PlanResponse,
    SubmitUtrRequest,
    SubscriptionResponse,
)
from app.services.payment import (
    build_upi_uri,
    calculate_discount,
    calculate_final_amount,
)
from app.services.plans import (
    PLANS,
    get_plan,
)


router = APIRouter(
    tags=["Payments"]
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _order_response(
    order: PaymentOrder,
) -> PaymentOrderResponse:

    return PaymentOrderResponse(
        id=order.id,
        plan_code=order.plan_code,
        amount_inr=float(order.amount_inr),
        discount_inr=float(order.discount_inr),
        final_amount_inr=float(
            order.final_amount_inr
        ),
        upi_vpa=order.upi_vpa,
        transaction_note=order.transaction_note,
        transaction_ref=order.transaction_ref,
        utr_reference=order.utr_reference,
        status=order.status,
        rejection_reason=order.rejection_reason,
        created_at=order.created_at,
        upi_uri=build_upi_uri(
            float(order.final_amount_inr),
            order.transaction_note,
            order.transaction_ref,
        ),
    )


def _find_coupon(
    db: Session,
    code: str,
) -> Coupon | None:

    if not code:
        return None

    normalized = code.strip().upper()

    return (
        db.query(Coupon)
        .filter(
            Coupon.code == normalized,
            Coupon.is_active == True,
        )
        .first()
    )


def _validate_coupon(
    db: Session,
    user_id: int,
    plan_code: str,
    coupon_code: str | None,
):
    """
    Returns:

        coupon
        discount
        original amount
        final amount
    """

    plan = get_plan(plan_code)

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Unknown subscription plan.",
        )

    amount = float(
        plan["price_inr"]
    )

    if not coupon_code:
        return (
            None,
            0.0,
            amount,
            amount,
        )

    coupon = _find_coupon(
        db,
        coupon_code,
    )

    if not coupon:
        raise HTTPException(
            status_code=400,
            detail="Invalid or inactive coupon.",
        )

    now = _utcnow()

    if coupon.valid_from:
        valid_from = coupon.valid_from

        if valid_from.tzinfo is None:
            valid_from = valid_from.replace(
                tzinfo=timezone.utc
            )

        if now < valid_from:
            raise HTTPException(
                status_code=400,
                detail="Coupon is not active yet.",
            )

    if coupon.valid_until:
        valid_until = coupon.valid_until

        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(
                tzinfo=timezone.utc
            )

        if now > valid_until:
            raise HTTPException(
                status_code=400,
                detail="Coupon has expired.",
            )

    if (
        coupon.max_uses is not None
        and coupon.used_count
        >= coupon.max_uses
    ):
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit reached.",
        )

    already_used = (
        db.query(CouponUsage)
        .filter(
            CouponUsage.coupon_id
            == coupon.id,
            CouponUsage.user_id
            == user_id,
        )
        .first()
    )

    if already_used:
        raise HTTPException(
            status_code=400,
            detail="You have already used this coupon.",
        )

    try:
        discount = calculate_discount(
            amount,
            coupon.discount_type,
            float(coupon.discount_value),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    final_amount = calculate_final_amount(
        amount,
        discount,
    )

    return (
        coupon,
        discount,
        amount,
        final_amount,
    )


@router.get(
    "/api/subscriptions/plans",
    response_model=list[PlanResponse],
)
def list_plans():

    return [
        PlanResponse(
            code=code,
            **plan,
        )
        for code, plan in PLANS.items()
    ]


@router.get(
    "/api/subscriptions/me",
    response_model=SubscriptionResponse | None,
)
def my_subscription(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.is_active == True,
        )
        .order_by(
            Subscription.end_date.desc()
        )
        .first()
    )

    if not sub:
        return None

    end_date = sub.end_date

    if end_date.tzinfo is None:
        end_date = end_date.replace(
            tzinfo=timezone.utc
        )

    if end_date <= _utcnow():

        sub.is_active = False

        db.commit()

        return None

    return sub


@router.post(
    "/api/payment/coupon/validate",
    response_model=CouponValidateResponse,
)
def validate_coupon(
    data: CouponValidateRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    plan_code = (
        data.plan_code
        .strip()
        .upper()
    )

    (
        coupon,
        discount,
        original_amount,
        final_amount,
    ) = _validate_coupon(
        db,
        user.id,
        plan_code,
        data.coupon_code,
    )

    return CouponValidateResponse(
        valid=True,
        coupon_code=coupon.code,
        original_amount=original_amount,
        discount_amount=discount,
        final_amount=final_amount,
        message="Coupon applied successfully.",
    )


@router.post(
    "/api/payment/initiate",
    response_model=PaymentOrderResponse,
    status_code=201,
)
def initiate_payment(
    data: InitiatePaymentRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    plan_code = (
        data.plan_code
        .strip()
        .upper()
    )

    plan = get_plan(
        plan_code
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Unknown subscription plan.",
        )

    (
        coupon,
        discount,
        original_amount,
        final_amount,
    ) = _validate_coupon(
        db,
        user.id,
        plan_code,
        data.coupon_code,
    )

    # If there is already a pending order for the
    # same plan and same final amount, reuse it.
    existing_query = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.user_id
            == user.id,
            PaymentOrder.plan_code
            == plan_code,
            PaymentOrder.final_amount_inr
            == final_amount,
            PaymentOrder.status
            == "PENDING",
        )
    )

    existing = (
        existing_query
        .order_by(
            PaymentOrder.created_at.desc()
        )
        .first()
    )

    if existing:
        return _order_response(
            existing
        )

    transaction_ref = (
        f"MS-{user.id}-"
        f"{int(_utcnow().timestamp())}-"
        f"{token_hex(4).upper()}"
    )

    transaction_note = (
        f"MauryaShaadi "
        f"{plan['name']} "
        f"{transaction_ref}"
    )

    order = PaymentOrder(
        user_id=user.id,
        plan_code=plan_code,
        amount_inr=original_amount,
        discount_inr=discount,
        final_amount_inr=final_amount,
        upi_vpa=settings.upi_vpa,
        transaction_note=transaction_note,
        transaction_ref=transaction_ref,
        status="PENDING",
        coupon_id=(
            coupon.id
            if coupon
            else None
        ),
    )

    db.add(order)

    db.commit()

    db.refresh(order)

    return _order_response(
        order
    )


@router.post(
    "/api/payment/{order_id}/submit-utr",
    response_model=PaymentOrderResponse,
)
def submit_utr(
    order_id: int,
    data: SubmitUtrRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    order = db.get(
        PaymentOrder,
        order_id,
    )

    if (
        not order
        or order.user_id != user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Payment order not found.",
        )

    if order.status not in {
        "PENDING",
        "REJECTED",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot submit UTR for "
                f"order status {order.status}."
            ),
        )

    utr = (
        data.utr_reference
        .strip()
        .upper()
    )

    if not utr:
        raise HTTPException(
            status_code=400,
            detail="UTR is required.",
        )

    # Don't allow same UTR on another payment.
    duplicate = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.utr_reference
            == utr,
            PaymentOrder.id
            != order.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "This UTR has already been "
                "submitted for another payment."
            ),
        )

    order.utr_reference = utr
    order.status = "SUBMITTED"
    order.rejection_reason = None

    db.commit()

    db.refresh(order)

    return _order_response(
        order
    )


@router.get(
    "/api/payments/history",
    response_model=list[
        PaymentOrderResponse
    ],
)
def payment_history(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    orders = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.user_id
            == user.id
        )
        .order_by(
            PaymentOrder.created_at.desc()
        )
        .all()
    )

    return [
        _order_response(order)
        for order in orders
    ]