from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.admin_deps import get_current_admin
from app.api.routes.payments import _order_response
from app.api.routes.profiles import profile_response
from app.db.session import get_db
from app.models.audit import record_audit
from app.models.payment import (
    Coupon,
    PaymentOrder,
    Subscription,
)
from app.models.profile import Profile
from app.models.user import User
from app.schemas.payment import (
    CouponCreateRequest,
    CouponResponse,
    PaymentOrderResponse,
    RejectPaymentRequest,
)
from app.schemas.profile import ProfileResponse
from app.services.plans import get_plan

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProfileRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


@router.get("/access-test")
def access_test(admin: User = Depends(get_current_admin)):
    return {"ok": True, "admin_id": admin.id, "message": "Admin access confirmed."}


@router.get("/stats")
def get_stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {
        "total": db.query(Profile).count(),
        "pending_review": db.query(Profile).filter(Profile.status == "PENDING_REVIEW").count(),
        "active": db.query(Profile).filter(Profile.status == "ACTIVE").count(),
        "draft": db.query(Profile).filter(Profile.status == "DRAFT").count(),
    }


@router.get("/profiles/pending", response_model=list[ProfileResponse])
def list_pending_profiles(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    profiles = (
        db.query(Profile)
        .filter(Profile.status == "PENDING_REVIEW")
        .order_by(Profile.updated_at.asc())
        .all()
    )
    return [profile_response(db, p) for p in profiles]


@router.get("/profiles", response_model=list[ProfileResponse])
def list_profiles(
    status_filter: str | None = None,
    search: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Profile)
    if status_filter:
        query = query.filter(Profile.status == status_filter.strip().upper())
    if search:
        query = query.filter(Profile.name.ilike(f"%{search.strip()}%"))
    profiles = query.order_by(Profile.updated_at.desc()).all()
    return [profile_response(db, p) for p in profiles]


@router.get("/profiles/{user_id}", response_model=ProfileResponse)
def get_profile_detail(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile_response(db, p)


@router.post("/profiles/{user_id}/approve", response_model=ProfileResponse)
def approve_profile(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found.")
    if p.status != "PENDING_REVIEW":
        raise HTTPException(status_code=409, detail=f"Cannot approve a profile in status {p.status}.")

    p.status = "ACTIVE"
    p.rejection_reason = None
    record_audit(db, admin.id, "PROFILE_APPROVE", target_user_id=user_id)
    db.commit()
    db.refresh(p)
    return profile_response(db, p)


@router.post("/profiles/{user_id}/reject", response_model=ProfileResponse)
def reject_profile(
    user_id: int,
    data: ProfileRejectRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found.")
    if p.status != "PENDING_REVIEW":
        raise HTTPException(status_code=409, detail=f"Cannot reject a profile in status {p.status}.")

    p.status = "DRAFT"
    p.rejection_reason = data.reason.strip()
    record_audit(db, admin.id, "PROFILE_REJECT", target_user_id=user_id, detail=p.rejection_reason)
    db.commit()
    db.refresh(p)
    return profile_response(db, p)


@router.get("/payments", response_model=list[PaymentOrderResponse])
def list_payments(
    status_filter: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(PaymentOrder)
    if status_filter:
        query = query.filter(PaymentOrder.status == status_filter.strip().upper())
    orders = query.order_by(PaymentOrder.created_at.desc()).all()
    return [_order_response(o) for o in orders]


@router.post("/payments/{order_id}/verify", response_model=PaymentOrderResponse)
def verify_payment(order_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    order = db.get(PaymentOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Payment order not found.")
    if order.status != "SUBMITTED":
        raise HTTPException(status_code=409, detail=f"Cannot verify an order in status {order.status}.")

    plan = get_plan(order.plan_code)
    if not plan:
        raise HTTPException(status_code=422, detail="This order references an unknown plan.")

    now = _utcnow()
    order.status = "VERIFIED"
    order.rejection_reason = None
    order.verified_by_user_id = admin.id
    order.verified_at = now

    db.query(Subscription).filter(
        Subscription.user_id == order.user_id,
        Subscription.is_active == True,  # noqa: E712
    ).update({"is_active": False})

    db.add(
        Subscription(
            user_id=order.user_id,
            plan_code=order.plan_code,
            start_date=now,
            end_date=now + timedelta(days=plan["duration_days"]),
            source_order_id=order.id,
        )
    )

    record_audit(db, admin.id, "PAYMENT_VERIFY", target_user_id=order.user_id, detail=order.transaction_ref)
    db.commit()
    db.refresh(order)
    return _order_response(order)


@router.post("/payments/{order_id}/reject", response_model=PaymentOrderResponse)
def reject_payment(
    order_id: int,
    data: RejectPaymentRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.get(PaymentOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Payment order not found.")
    if order.status != "SUBMITTED":
        raise HTTPException(status_code=409, detail=f"Cannot reject an order in status {order.status}.")

    order.status = "REJECTED"
    order.rejection_reason = data.reason.strip()
    record_audit(db, admin.id, "PAYMENT_REJECT", target_user_id=order.user_id, detail=order.rejection_reason)
    db.commit()
    db.refresh(order)
    return _order_response(order)


@router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("/coupons", response_model=CouponResponse, status_code=201)
def create_coupon(
    data: CouponCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    code = data.code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="A coupon with this code already exists.")

    discount_type = data.discount_type.strip().upper()
    if discount_type not in {"PERCENT", "FIXED"}:
        raise HTTPException(status_code=422, detail="discount_type must be PERCENT or FIXED.")

    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=data.discount_value,
        max_uses=data.max_uses,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        created_by_admin_id=admin.id,
    )
    db.add(coupon)
    record_audit(db, admin.id, "COUPON_CREATE", detail=code)
    db.commit()
    db.refresh(coupon)
    return coupon
