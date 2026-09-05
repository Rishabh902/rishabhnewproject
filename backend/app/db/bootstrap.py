from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.session import Base, engine
from app.models.user import User


def ensure_schema_compatibility() -> None:
    """Non-destructive compatibility migration for databases created by Phase 3.

    New installations are created by SQLAlchemy metadata. Existing databases
    receive additive columns so upgrading the ZIP does not require deleting data.
    For production, these statements should be represented by versioned Alembic
    migrations before the first live deployment.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        if "users" in tables:
            existing = {c["name"] for c in inspector.get_columns("users")}
            additions = {
                "profile_for": "VARCHAR(40) NOT NULL DEFAULT 'self'",
                "relationship": "VARCHAR(80)",
                "registration_location": "VARCHAR(200)",
            }
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN "{name}" {definition}'))

        if "profiles" in tables:
            existing = {c["name"] for c in inspector.get_columns("profiles")}
            additions = {
                "caste": "VARCHAR(150)",
                "degree": "VARCHAR(200)",
                "weight_kg": "INTEGER",
                "state": "VARCHAR(100)",
                "district": "VARCHAR(120)",
                "city_or_village": "VARCHAR(150)",
            }
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE profiles ADD COLUMN "{name}" {definition}'))

        if "payment_orders" in tables:
            existing = {c["name"] for c in inspector.get_columns("payment_orders")}
            additions = {
                "coupon_id": "INTEGER",
                "order_reference": "VARCHAR(64)",
                "gateway": "VARCHAR(30) DEFAULT 'razorpay'",
                "gateway_order_id": "VARCHAR(80)",
                "original_amount_inr": "NUMERIC(10,2)",
                "discount_amount_inr": "NUMERIC(10,2) DEFAULT 0",
                "tax_amount_inr": "NUMERIC(10,2) DEFAULT 0",
                "final_amount_inr": "NUMERIC(10,2)",
                "currency": "VARCHAR(3) DEFAULT 'INR'",
                "failure_reason": "TEXT",
            }
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE payment_orders ADD COLUMN "{name}" {definition}'))
            conn.execute(text("UPDATE payment_orders SET order_reference = COALESCE(order_reference, 'LEGACY-' || id::text)"))
            conn.execute(text("UPDATE payment_orders SET original_amount_inr = COALESCE(original_amount_inr, amount_inr)"))
            conn.execute(text("UPDATE payment_orders SET final_amount_inr = COALESCE(final_amount_inr, amount_inr)"))
            conn.execute(text("UPDATE payment_orders SET discount_amount_inr = COALESCE(discount_amount_inr, 0), tax_amount_inr = COALESCE(tax_amount_inr, 0), currency = COALESCE(currency, 'INR'), gateway = COALESCE(gateway, 'legacy_upi')"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_orders_order_reference ON payment_orders(order_reference)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_orders_gateway_order_id ON payment_orders(gateway_order_id) WHERE gateway_order_id IS NOT NULL"))

        if "subscriptions" in tables:
            existing = {c["name"] for c in inspector.get_columns("subscriptions")}
            additions = {
                "payment_id": "INTEGER",
                "status": "VARCHAR(30)",
                "auto_renew": "BOOLEAN NOT NULL DEFAULT FALSE",
                "cancelled_at": "TIMESTAMPTZ",
            }
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE subscriptions ADD COLUMN "{name}" {definition}'))
            conn.execute(text("UPDATE subscriptions SET status = CASE WHEN is_active = TRUE AND end_date >= NOW() THEN 'ACTIVE' WHEN is_active = TRUE THEN 'EXPIRED' ELSE 'CANCELLED' END WHERE status IS NULL"))



def seed_single_admin() -> None:
    """Create the configured admin account only when credentials are supplied.

    Public registration always forces role='user', so admins cannot be created
    through the registration API.
    """
    if not settings.admin_login_id or not settings.admin_password:
        return
    with Session(engine) as db:
        # Keep one authoritative admin account. Any older manually-created admin
        # account is demoted so the public system has a single admin identity.
        db.query(User).filter(User.role == "admin", User.email != settings.admin_login_id).update({"role": "user"}, synchronize_session=False)
        admin = db.query(User).filter(User.email == settings.admin_login_id).first()
        if admin:
            changed = False
            if admin.role != "admin":
                admin.role = "admin"
                changed = True
            # Keep the documented development admin credentials deterministic.
            if not verify_password(settings.admin_password, admin.password_hash):
                admin.password_hash = hash_password(settings.admin_password)
                changed = True
            if not admin.is_active:
                admin.is_active = True
                changed = True
            if not admin.is_email_verified:
                admin.is_email_verified = True
                changed = True
            if changed:
                db.commit()
            return

        admin = User(
            email=settings.admin_login_id,
            password_hash=hash_password(settings.admin_password),
            profile_for="self",
            relationship=None,
            registration_location="Admin",
            is_email_verified=True,
            is_phone_verified=False,
            is_active=True,
            role="admin",
        )
        db.add(admin)
        db.commit()
