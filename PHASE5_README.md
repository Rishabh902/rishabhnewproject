# MauryaShaadi Phase 5 — Interests, Matches, Shortlist & Notifications

Phase 5 is implemented on top of the Phase 3/4 project.

## Business flow

```text
ACTIVE Profile A
      |
      | Send Interest
      v
Interest(PENDING)
      |
      +--------------------+
      |                    |
   Reject               Accept
      |                    |
REJECTED             MATCH CREATED
                           |
                    Notifications
                           |
                    Confirmed Match
```

## Backend

### New models

- `Interest`
- `Match`
- `Shortlist`
- `Notification`

### New schemas

`backend/app/schemas/phase5.py`

### New service

`backend/app/services/phase5.py`

### New router

`backend/app/api/routes/phase5.py`

### Endpoints

#### Interests

- `POST /api/interests`
- `GET /api/interests/sent`
- `GET /api/interests/received`
- `POST /api/interests/{id}/accept`
- `POST /api/interests/{id}/reject`
- `DELETE /api/interests/{id}`

#### Matches

- `GET /api/matches`
- `GET /api/matches/{user_id}`

#### Shortlists

- `POST /api/shortlists`
- `GET /api/shortlists`
- `DELETE /api/shortlists/{profile_user_id}`

#### Notifications

- `GET /api/notifications`
- `POST /api/notifications/{id}/read`
- `DELETE /api/notifications/{id}`

## Security/business rules

- User must have an `ACTIVE` profile to use Phase 5 actions.
- Target profile must also be `ACTIVE`.
- Users cannot send interest to themselves.
- Duplicate active interests are blocked.
- Only the receiver can accept/reject an interest.
- An accepted interest creates a canonical user pair in `matches`.
- Confirmed matches are available through `/api/matches`.
- Shortlist entries are unique per user/profile pair.
- Notifications are private to their recipient.
- Notification read/delete operations are owner-only.

## Database

For a fresh database, `DATABASE_SCHEMA.sql` includes the Phase 5 tables.

For an existing database, run:

`backend/migrations/phase5_interest_match_shortlist_notification.sql`

The application also imports the models and `Base.metadata.create_all()` will create missing Phase 5 tables during development. Use a proper migration tool such as Alembic for production schema changes.

## Frontend

New pages:

- `/interests`
- `/shortlist`
- `/notifications`

Updated pages:

- `/matches` — now shows confirmed matches and recommendations.
- `/profile/:userId` — Add/Remove Shortlist and Send Interest.
- `/dashboard` — quick links to Phase 5 pages.

## Run

### Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The uploaded archive contained platform-specific `node_modules`; do not copy that folder between Windows/Linux machines. Run `npm install` on the machine where you develop.
