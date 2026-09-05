# MauryaShaadi — Phase 4

## What was fixed

The previous matching implementation could return zero results even with many approved profiles because location, profession and education preferences were treated as hard rejection rules. Phase 4 changes these three dimensions to ranking signals.

### Compatibility score

- Location: 40%
- Profession: 30%
- Qualification: 30%

### Hard compatibility filters

- Candidate must be `ACTIVE`.
- The current user must be `ACTIVE`.
- Gender compatibility is enforced when both genders are provided.
- Configured minimum/maximum age and height are enforced.

### Ranking

The engine normalizes common text variations and recognizes related groups such as:

- Delhi / Noida / Gurgaon / Ghaziabad / Delhi NCR
- Software Engineer / Software Developer / Developer
- Data Scientist / Data Analyst / ML Engineer
- B.Tech / BTech / Bachelor of Technology
- MBA / MCA / B.Com and other common qualifications

Recommendations are sorted from highest compatibility to lowest.

## Run

### Backend

```bash
cd backend
.venv\\Scripts\\activate
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `/matches` after logging in with an approved (`ACTIVE`) user.

## Diagnose the 50 test records

Run `PHASE4_MATCHING_TEST.sql` in PostgreSQL. In particular, confirm that there are multiple `ACTIVE` profiles and both compatible genders.

## Important

The matching engine is intentionally explainable and deterministic. It is an AI-style semantic ranking layer, not a trained neural network. This keeps the project dependency-light and makes each recommendation score auditable. A future embedding/ML model can replace the scoring internals without changing the API contract.
