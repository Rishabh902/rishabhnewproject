# MauryaShaadi — Complete Implemented Flow

## 1. Purpose

MauryaShaadi is a community-focused matrimonial application. The current implementation covers the controlled registration, profile creation, OTP activation, password/OTP login, profile completion, admin approval/rejection and approved-profile matching flow.

The implementation is based on the supplied MauryaShaadi project and system documentation. The documented target requires OTP verification, profile completion, permanent address and preferred/looking location, photo processing, Pending Review, admin approval and matching restricted to approved profiles.

## 2. Actual User Flow

```text
Landing Page
   |
   v
Register
   |
   +--> Phone (required)
   +--> Email (optional)
   +--> Password
   +--> Who is making the profile?
   +--> Relationship (required when not Self)
   +--> Registration / looking location
   |
   v
Account created as USER + inactive
   |
   v
Initial Profile
   +--> Full name
   +--> Gender
   +--> Date of birth
   +--> Community (optional)
   +--> Permanent address (required)
   +--> Preferred / looking location (required)
   |
   v
Registration OTP verification
   |
   v
Account ACTIVE
   |
   +-----------------------------+
   |                             |
   v                             v
Password Login                OTP Login
   |                             |
   +-------------+---------------+
                 |
                 v
          User Dashboard
                 |
                 v
          Complete Profile
                 |
       +---------+---------+
       |                   |
       v                   v
Partner Preferences     Photo upload
       |                   |
       +---------+---------+
                 |
                 v
         Submit for Review
                 |
                 v
          PENDING_REVIEW
                 |
          +------+------+
          |             |
          v             v
       APPROVE        REJECT
          |             |
          v             v
        ACTIVE         DRAFT
          |             |
          v             |
       Matching <-------+
```

## 3. Registration Rules

- Public registration can only create `role=user` accounts.
- Admin accounts are never created through `/register`.
- A mobile number is required because mobile OTP verification is mandatory before profile submission.
- The user must select who is making the profile.
- If the profile is being made for someone other than the user, a relationship is required.
- Registration/looking location is required.
- An inactive account cannot login.
- A registration session token is returned after registration and is required to save the initial profile and verify the registration OTP.

## 4. Registration Initial Profile

The registration profile is intentionally smaller than the full profile. It establishes the identity of the profile before activation.

Required:

- Full name
- Gender
- Date of birth
- Permanent address
- Preferred / looking location

Optional:

- Community

The person must be at least 18 years old.

## 5. OTP Flow

### Registration OTP

```text
POST /api/auth/register
       |
       v
OTP issued
       |
POST /api/auth/register/profile
       |
POST /api/auth/otp/verify
       |
       v
user.is_active = true
user.is_phone_verified = true
```

### Login OTP

```text
POST /api/auth/login/otp/request
       |
       v
POST /api/auth/login/otp/verify
       |
       v
JWT access + refresh tokens
```

OTP rules:

- Six digits
- Configurable expiry
- Configurable maximum attempts
- OTP values are hashed in the database
- Development mode returns `dev_otp` for local testing only

## 6. Password Login

```text
POST /api/auth/login
```

The password is verified against the stored password hash. Only active accounts can login.

## 7. Full Profile Flow

After login, the user can complete:

- Personal details
- Gothra/community
- Education
- Profession
- Income
- Height
- Permanent address
- Preferred / looking location
- Family details
- Partner preferences
- Profile photo

Permanent address and preferred/looking location remain mandatory for submission.

## 8. Profile State Machine

```text
DRAFT
  |
  v
PENDING_REVIEW
  |        \
  |         \
  |          v
  |        DRAFT (Rejected + reason)
  |
  v
ACTIVE
```

Current rules:

- `DRAFT`: editable.
- `PENDING_REVIEW`: locked for normal user editing.
- `ACTIVE`: approved and visible in matching.
- Rejection returns the profile to `DRAFT` and stores `rejection_reason`.
- After correction, the user saves the profile and submits again.
- Only `ACTIVE` profiles enter matching.

## 9. Admin Account

There is one application admin account.

**Admin login ID:** `admin@mauryashaadi.com`

**Admin password:** Set `ADMIN_PASSWORD` in `backend/.env`; no production credential is stored in the repository.

The admin is seeded automatically at backend startup.

Public registration always forces `role=user`. The bootstrap process keeps the configured admin as the single admin identity and demotes older manually-created admin roles.

For production, replace the development password through environment variables/secrets before deployment.

## 10. Admin Flow

```text
Admin Login
    |
    v
GET /api/admin/profiles/pending
    |
    v
Review profile
    |
    +---- Approve ----> ACTIVE
    |
    +---- Reject -----> DRAFT + rejection_reason
```

Admin endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/access-test` | Verify admin authorization |
| GET | `/api/admin/profiles/pending` | Pending review queue |
| GET | `/api/admin/profiles/{user_id}` | View profile for review |
| POST | `/api/admin/profiles/{user_id}/approve` | Approve profile |
| POST | `/api/admin/profiles/{user_id}/reject` | Reject with reason |

Every admin endpoint requires a valid JWT and `role=admin`.

## 11. Matching Flow

Matching is available only when the current user's profile is `ACTIVE`.

```text
User ACTIVE
   |
   v
Load ACTIVE candidates
   |
   v
Exclude current user
   |
   v
Gender compatibility
   |
   v
Current user's partner preferences
   |
   v
Candidate's partner preferences
   |
   v
Compatibility score
   |
   v
Sorted matching profiles
```

Endpoint:

```text
GET /api/profiles/matches
```

The matching response intentionally does not expose the permanent address.

Only approved/active profiles can appear in the candidate pool.

## 12. Main API List

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/register/profile`
- `POST /api/auth/otp/request`
- `POST /api/auth/otp/verify`
- `POST /api/auth/login`
- `POST /api/auth/login/otp/request`
- `POST /api/auth/login/otp/verify`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Profiles

- `GET /api/profiles/me`
- `PUT /api/profiles/me`
- `POST /api/profiles/me/complete`
- `GET /api/profiles/me/preferences`
- `PUT /api/profiles/me/preferences`
- `POST /api/profiles/me/photo`
- `DELETE /api/profiles/me/photo`
- `GET /api/profiles/{user_id}`
- `GET /api/profiles/{user_id}/photo`
- `GET /api/profiles/matches`

### Verification

- `GET /api/verification/status`
- `POST /api/verification/parent/request`
- `POST /api/verification/parent/verify`
- `POST /api/verification/identity/request`
- `POST /api/verification/identity/verify`

### Admin

- `GET /api/admin/access-test`
- `GET /api/admin/profiles/pending`
- `GET /api/admin/profiles/{user_id}`
- `POST /api/admin/profiles/{user_id}/approve`
- `POST /api/admin/profiles/{user_id}/reject`

## 13. Frontend Routes

### Public

- `/`
- `/register`
- `/login`

### User

- `/dashboard`
- `/complete-profile`
- `/verification`

### Admin

- `/admin`
- `/admin/profiles/:userId`

## 14. Database Tables Used by Current Flow

- `users`
- `profiles`
- `partner_preferences`
- `otps`
- `verifications`

## 15. Important User Columns

`users`:

- `id`
- `phone`
- `email`
- `password_hash`
- `profile_for`
- `relationship`
- `registration_location`
- `is_phone_verified`
- `is_email_verified`
- `is_active`
- `role`
- timestamps

## 16. Important Profile Columns

`profiles`:

- `id`
- `user_id`
- `name`
- `gender`
- `date_of_birth`
- `gothra`
- `community`
- `education`
- `profession`
- `income`
- `height_cm`
- `permanent_address`
- `preferred_location`
- `family_details`
- `photo_path`
- `status`
- `rejection_reason`
- timestamps

## 17. Database Compatibility

The supplied project already has the Phase 1/2 database tables. Phase 3 adds three registration-context columns to `users`:

```sql
profile_for VARCHAR(40) NOT NULL DEFAULT 'self'
relationship VARCHAR(80)
registration_location VARCHAR(200)
```

The backend runs a small compatibility migration at startup so an existing database is not dropped or recreated. No user data is deleted.

For production, replace this bootstrap migration with Alembic migrations.

## 18. Photo Security

- Only JPG, PNG and WEBP are accepted.
- Maximum upload size is 5 MB.
- Images are converted to RGB.
- Images are resized to a maximum of 1200x1200.
- `MauryaShaadi.com` watermark is applied.
- Only the owner, an admin, or a viewer of an ACTIVE profile can access the image endpoint.

## 19. Run the Project

### Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## 20. Full Test Sequence

### Test A — Register

1. Open `/register`.
2. Enter mobile number.
3. Optionally enter email.
4. Enter password.
5. Select who is making the profile.
6. Select/enter relationship when required.
7. Enter location.
8. Continue.

### Test B — Initial Profile

1. Enter name.
2. Select gender.
3. Enter DOB.
4. Enter permanent address.
5. Enter preferred/looking location.
6. Save profile.

### Test C — Registration OTP

Use the development OTP displayed by the backend/frontend.

After successful verification, the account becomes active.

### Test D — Login

Test both:

- Password login
- OTP login

### Test E — Complete Profile

After login:

1. Open Complete Profile.
2. Add education/profession/income/height.
3. Add family details.
4. Save partner preferences.
5. Upload photo.
6. Submit for admin review.

### Test F — Admin

1. Open `/login`.
2. Login using the single admin account.
3. You are redirected to `/admin`.
4. Open a pending profile.
5. Review it.
6. Approve it.

### Test G — Matching

1. Login as the approved user.
2. Open dashboard.
3. Matching is available only after the profile is `ACTIVE`.
4. Only ACTIVE profiles appear.

### Test H — Rejection

1. Submit another profile.
2. Admin rejects it with a reason.
3. User sees the reason.
4. User corrects the profile.
5. User resubmits.
6. Admin can approve again.

## 21. Development Notes

- Do not create admin users through the public registration page.
- Do not store plaintext passwords in the database.
- Keep `JWT_SECRET_KEY` private.
- Keep database credentials private.
- Development `dev_otp` must be disabled in production.
- Production should use HTTPS, real SMS/email OTP delivery, Alembic migrations, secure object storage and rate limiting.

## 22. Next Project Phase

The next phase after this flow is the richer search/matching system: filters, recommendation scoring, pagination, shortlist, interests, notifications and then match/chat functionality.
