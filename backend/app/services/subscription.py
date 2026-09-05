from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.payment import Payment, Subscription, SubscriptionPlan


def utcnow():
    return datetime.now(timezone.utc)


def activate_subscription(db: Session, user_id: int, plan: SubscriptionPlan, payment_id: int, source_order_id: int | None = None) -> Subscription:
    now = utcnow()
    active = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "ACTIVE")
        .order_by(Subscription.end_date.desc())
        .first()
    )
    if active:
        current_end = active.end_date if active.end_date.tzinfo else active.end_date.replace(tzinfo=timezone.utc)
        start = current_end if current_end > now else now
        active.end_date = start.replace() + timedelta(days=plan.duration_days)
        active.plan_code = plan.code
        active.payment_id = payment_id
        active.status = "ACTIVE"
        active.updated_at = now
        return active

    sub = Subscription(
        user_id=user_id,
        plan_code=plan.code,
        payment_id=payment_id,
        source_order_id=source_order_id,
        start_date=now,
        end_date=now + timedelta(days=plan.duration_days),
        status="ACTIVE",
    )
    db.add(sub)
    return sub


def expire_old_subscriptions(db: Session) -> int:
    now = utcnow()
    rows = db.query(Subscription).filter(Subscription.status == "ACTIVE", Subscription.end_date < now).all()
    for row in rows:
        row.status = "EXPIRED"
        row.updated_at = now
    if rows:
        db.commit()
    return len(rows)


def current_subscription(db: Session, user_id: int) -> Subscription | None:
    now = utcnow()
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "ACTIVE", Subscription.end_date >= now)
        .order_by(Subscription.end_date.desc())
        .first()
    )
    return sub


def max_match_score(db: Session, user_id: int) -> int:
    sub = current_subscription(db, user_id)
    if not sub:
        return 0
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == sub.plan_code).first()
    return plan.max_match_score if plan else 0
