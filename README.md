# MauryaShaadi Phase 3 — Complete Registration, Approval & Matching Flow

Read `docs/PROJECT_DOCUMENTATION.md` for the complete flow, API list, database changes and test sequence.

## Admin account

- Login ID: `admin@mauryashaadi.com`
- Password: Set `ADMIN_PASSWORD` in `backend/.env`

The admin is seeded by the backend. It is not possible to register an admin through the public registration form.

## Start

Backend:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Swagger: `http://localhost:8000/docs`
Frontend: `http://localhost:5173`

## Phase 6 — Production Subscription & Payments

The subscription/payment module now uses a gateway-backed architecture:

- AI Discovery — ₹49/month — up to 50% AI compatibility
- AI Smart Match — ₹199/month — up to 75% AI compatibility
- AI Premium Match — ₹499/month — up to 100% AI compatibility when available
- Backend-calculated coupon discounts
- Razorpay order creation
- Server-side payment signature verification
- Razorpay webhook verification and idempotency
- Subscription activation only after a captured payment is confirmed
- Payment/order/subscription records kept separate
- Manual UTR verification is no longer the normal production payment path

Configure `backend/.env` from `backend/.env.example` before running the payment flow.
Use Razorpay Test Mode keys for staging; switch to Live Mode only after completing gateway onboarding and webhook configuration.
