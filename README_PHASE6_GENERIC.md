# Generic Matrimony Platform — Updated Flow

This project is no longer community-specific. It supports profiles from any caste/community.

## New flow

1. Register with mobile, email, password and confirm password.
2. Enter basic profile: name, gender, DOB, caste/community, state, district, city/village and address.
3. Verify mobile OTP.
4. Login with password or OTP.
5. Complete every profile field.
6. Select height, weight, education level, degree, profession, income, caste/community and location.
7. Select partner preferences.
8. Upload a minimum of 10 photos (maximum 20).
9. Submit profile.
10. Admin reviews and approves/rejects.
11. Approved profiles appear in search/matching.
12. Interest → accept/reject → match → shortlist → notifications.
13. Chat unlocks after a match.
14. Subscription/payment features remain available for the later phases.

## Password reset

Login → Forgot password → enter registered email → secure one-time reset link is emailed → Create new password → Login.

Configure SMTP in `backend/.env` using `backend/.env.example`.

## Database

For an existing PostgreSQL database run:
`backend/migrations/phase6_generic_matrimony.sql`

The application also performs additive compatibility checks during startup.

## Local setup

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and set DATABASE_URL and JWT_SECRET_KEY.
uvicorn app.main:app --reload
```

Do not use `localhost:5432` unless PostgreSQL is actually running locally. Neon/hosted PostgreSQL requires its own connection string.

### Frontend

Use Node 20.19+ (or a current supported Node release).

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` if the API is running locally.

## Production

- Use managed PostgreSQL (for example Neon).
- Use object storage/CDN for profile media rather than local disk.
- Configure real SMTP.
- Configure a real SMS/OTP provider.
- Restrict CORS to the production frontend.
- Use HTTPS.
- Keep secrets out of source control.
- Run versioned database migrations before deployment.
