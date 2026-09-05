# Phase 5 Implementation Changelog

Implemented all four Phase-5 modules requested by the MauryaShaadi system blueprint:

1. Interests
2. Confirmed Matches
3. Shortlists
4. Notifications

## Backend files added

- `backend/app/models/interest.py`
- `backend/app/models/match.py`
- `backend/app/models/shortlist.py`
- `backend/app/models/notification.py`
- `backend/app/schemas/phase5.py`
- `backend/app/services/phase5.py`
- `backend/app/api/routes/phase5.py`
- `backend/migrations/phase5_interest_match_shortlist_notification.sql`

## Existing backend files updated

- `backend/app/models/__init__.py`
- `backend/app/main.py`
- `DATABASE_SCHEMA.sql`

## Frontend files added

- `frontend/src/pages/Interests.jsx`
- `frontend/src/pages/Shortlist.jsx`
- `frontend/src/pages/Notifications.jsx`

## Existing frontend files updated

- `frontend/src/App.jsx`
- `frontend/src/pages/ProfileView.jsx`
- `frontend/src/pages/Matches.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/styles.css`

## API contract

### Interests

`POST /api/interests`

```json
{"receiver_id": 12}
```

`GET /api/interests/sent`

`GET /api/interests/received`

`POST /api/interests/{id}/accept`

`POST /api/interests/{id}/reject`

`DELETE /api/interests/{id}`

### Matches

`GET /api/matches`

`GET /api/matches/{user_id}`

### Shortlist

`POST /api/shortlists`

```json
{"profile_user_id": 12}
```

`GET /api/shortlists`

`DELETE /api/shortlists/{profile_user_id}`

### Notifications

`GET /api/notifications`

`POST /api/notifications/{id}/read`

`DELETE /api/notifications/{id}`

## Important behavior

- Only ACTIVE profiles can send interests or manage shortlists.
- Only ACTIVE target profiles can receive interests or be shortlisted.
- Self-interest and self-shortlisting are blocked.
- Duplicate shortlist entries are blocked by a database constraint.
- Duplicate interests are blocked by a database constraint and API validation.
- Only the receiver can accept/reject an interest.
- Accepting an interest creates one canonical match pair.
- Accepted interests generate match/acceptance notifications.
- Received interests generate `INTEREST_RECEIVED` notifications.
- Notification read/delete operations are recipient-only.
- Confirmed matches are separate from recommendation results.

## Verification performed

- Python backend source compiled successfully with `python -m compileall`.
- Phase 5 API integration was exercised with an isolated SQLite test database: send interest → receive → accept → match creation → shortlist → notifications all passed.
- The existing frontend dependency tree in the supplied ZIP contains platform-specific native packages, so its local Vite build cannot be trusted on Linux. On Windows/macOS/Linux, remove the supplied `node_modules` and run `npm install` before `npm run build`.
