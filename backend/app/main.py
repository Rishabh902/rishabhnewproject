from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter
from app.core.config import settings
from app.db.session import Base, engine
from app.db.bootstrap import ensure_schema_compatibility, seed_single_admin

# Load models so SQLAlchemy knows about all tables.
from app.models import (  # noqa: F401
    User,
    OTPCode,
    Profile,
    PartnerPreference,
    Verification,
    Interest,
    Match,
    Shortlist,
    Notification,
)

from app.models.chat import Message  # noqa: F401
from app.models.payment import PaymentOrder, Subscription  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401

from app.api.routes.auth import router as auth_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.verification import router as verification_router
from app.api.routes.admin import router as admin_router
from app.api.routes.phase5 import router as phase5_router
from app.api.routes.chat import router as chat_router
from app.api.routes.payments import router as payments_router
from app.models.payment import PaymentOrder, Subscription


# ---------------------------------------------------------
# Database startup
# ---------------------------------------------------------

Base.metadata.create_all(bind=engine)

ensure_schema_compatibility()
seed_single_admin()


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: {
        "detail": "Rate limit exceeded. Please try again later."
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(verification_router)
app.include_router(admin_router)
app.include_router(phase5_router)
app.include_router(chat_router)
app.include_router(payments_router)


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
    }