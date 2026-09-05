# MauryaShaadi Backend

Run:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

The backend automatically creates/updates the single configured admin account from `.env` and never creates admins through public registration.
