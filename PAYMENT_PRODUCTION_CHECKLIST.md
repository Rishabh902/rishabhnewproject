# MauryaShaadi — Phase 6 Payment/Subscription Production Checklist

## Plans
- AI Discovery: ₹49/month, max AI compatibility access 50%
- AI Smart Match: ₹199/month, max AI compatibility access 75%
- AI Premium Match: ₹499/month, max AI compatibility access 100% when available

## Backend flow
1. User selects a plan.
2. Optional coupon is validated on the server.
3. Server calculates the final amount.
4. Server creates a Razorpay order using the final amount in paise.
5. Frontend opens Razorpay Checkout with the server-created order ID.
6. Browser callback is sent back to the server.
7. Server verifies the payment signature and fetches the payment status.
8. Subscription is activated only after a captured payment with the expected amount.
9. Razorpay webhook is verified from the raw request body and processed idempotently.
10. Duplicate callbacks/webhooks do not create duplicate payments or subscriptions.

## Environment
Set these in `backend/.env` and never commit real values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ADMIN_LOGIN_ID`
- `ADMIN_PASSWORD`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`

Use Razorpay Test Mode keys during staging. Switch to Live Mode only after business/gateway onboarding is complete.

## Required gateway configuration before launch
- Enable the payment methods you want in Razorpay Checkout.
- Configure a HTTPS webhook endpoint at `/api/payments/webhook`.
- Subscribe to at least `payment.captured` and/or `order.paid` events.
- Use the same webhook secret in the Razorpay dashboard and `RAZORPAY_WEBHOOK_SECRET`.
- Verify a successful test payment, failed payment, duplicate callback, duplicate webhook, wrong amount and invalid signature before going live.

## Important
The application no longer uses manual UTR entry as the normal production payment flow. The old Phase-3 UPI/UTR code is retained only as database compatibility fields for safe migration.
