# Rihla Backend

FastAPI + PostgreSQL backend for the Rihla community ride-sharing app (SDG 11 project).

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ running locally (or any accessible host)

---

## Setup

### 1 — Create & activate a virtual environment

```powershell
cd rihla-backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate   # macOS / Linux
```

### 2 — Install dependencies

```powershell
pip install -r requirements.txt
```

### 3 — Configure environment

```powershell
copy .env.example .env
```

Edit `.env` and fill in:

| Variable | Example |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:secret@localhost:5432/rihla` |
| `JWT_SECRET` | any long random string, e.g. `openssl rand -hex 32` |
| `CORS_ORIGINS` | `http://127.0.0.1:5500` (wherever `rihla_1.html` is served from) |
| `SMTP_*` | leave blank to log emails to stdout instead of sending |

### 4 — Create the database

```sql
-- in psql:
CREATE DATABASE rihla;
```

### 5 — Run Alembic migrations

```powershell
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 6 — Seed the community

```powershell
python -m scripts.seed
```

This inserts **City University Cyberjaya Campus** (code `CITYU-2026`) once.
Running it again is safe — it's idempotent.

### 7 — Start the server

```powershell
uvicorn app.main:app --reload
```

The API is now live at `http://127.0.0.1:8000`.
Interactive docs: **http://127.0.0.1:8000/docs**

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | ❌ | Register; returns token + user |
| `POST` | `/auth/login` | ❌ | Login; returns token + user |
| `POST` | `/community/verify` | ✅ | Verify community code; sets community on user |
| `GET` | `/rides` | ✅ | List active/full rides in user's community |
| `POST` | `/rides` | ✅ | Post a new ride |
| `DELETE` | `/rides/{id}` | ✅ | Cancel a ride (soft delete); emails riders |
| `POST` | `/rides/{id}/join` | ✅ | Join a ride (concurrency-safe) |
| `GET` | `/leaderboard` | ✅ | Monthly leaderboard (`?month=YYYY-MM`) |
| `GET` | `/users/me` | ✅ | Current user profile + live stats |
| `PATCH` | `/users/me` | ✅ | Update name and/or about |

All protected endpoints require `Authorization: Bearer <token>`.

---

## Error shape

Every error response is:
```json
{ "error": "human-readable message" }
```

---

## CORS

The `CORS_ORIGINS` env var accepts a comma-separated list of origins.
Default: `http://127.0.0.1:5500` (Live Server default used by VS Code).

---

## Email notifications

Cancelling a ride sends one email per rider:
- **Subject:** `Your ride to {destination} was cancelled`
- **Body:** names the driver, destination, date, and time.

When `SMTP_HOST` is not set (the default for local dev), the email is
printed to stdout instead — the server never crashes either way.

---

## Concurrency — seat booking

`POST /rides/{id}/join` uses `SELECT ... FOR UPDATE` inside a transaction.
This means exactly one of two simultaneous requests for the last seat
will succeed; the other gets **409 This ride is full.**

---

## Project structure

```
rihla-backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, routers, exception handlers
│   ├── config.py            # pydantic-settings — reads .env
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── exceptions.py        # AppException hierarchy + global handlers
│   ├── models/              # ORM models (User, Community, Ride, RideJoin)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # Route handlers (auth, community, rides, leaderboard, users)
│   ├── auth/                # JWT + bcrypt + get_current_user dependency
│   └── services/
│       └── notifications.py # send_email() with stdout fallback
├── alembic/                 # Alembic migrations
├── scripts/
│   └── seed.py              # Seeds CITYU-2026 community
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```
