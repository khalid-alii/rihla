# Rihla — Community Ride-Sharing

> *Rihla* (Arabic for "Journey") is a community-scoped carpooling web app. It supports **SDG 11: Sustainable Cities and Communities** by reducing single-occupancy vehicle commutes.

**Live App:** https://rihla-eosin.vercel.app  
**API Docs:** https://rihla-api-n289.onrender.com/docs

---

## Tech Stack

| Layer | Technology | Hosting |
|---|---|---|
| Frontend | HTML, CSS, Vanilla JS | Vercel |
| Backend | Python, FastAPI | Render.com |
| Database | PostgreSQL, SQLAlchemy | Neon.tech |

---

## Features

-  JWT authentication with bcrypt password hashing
-  Community-gated access via unique codes (e.g. `CITYU-2026`)
-  Post, join, and cancel rides in real-time
-  Monthly leaderboard ranked by carpooling activity
-  Concurrency-safe seat booking (no double-booking)
-  Email notifications when a ride is cancelled

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL installed locally

### 1. Clone the repository
```bash
git clone https://github.com/khalid-alii/rihla.git
cd rihla
```

### 2. Create the database
```bash
psql -U postgres
CREATE DATABASE rihla;
\q
```

### 3. Set up the backend
```bash
cd rihla-backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your details:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/rihla
JWT_SECRET=any-random-secret-string
CORS_ORIGINS=http://127.0.0.1:5500
```

### 5. Run database migrations & seed
```bash
.venv\Scripts\alembic.exe upgrade head
python -m scripts.seed
```

### 6. Start the backend
```bash
.venv\Scripts\uvicorn.exe app.main:app --reload
# API now running at http://127.0.0.1:8000
```

### 7. Open the frontend
Open `index.html` with VS Code's **Live Server** extension.  
Then visit `http://127.0.0.1:5500/index.html` and register using the code **`CITYU-2026`**.

---

## Project Structure

```
rihla/
├── index.html                  # Frontend (Single Page Application)
├── rihla-backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # SQLAlchemy DB connection
│   │   ├── auth/               # JWT & bcrypt security
│   │   ├── models/             # Database table definitions
│   │   ├── routers/            # API endpoints
│   │   └── schemas/            # Request/response data shapes
│   ├── alembic/                # Database migration scripts
│   ├── scripts/seed.py         # Seeds the CITYU-2026 community
│   └── requirements.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login and receive a JWT token |
| POST | `/community/verify` | Verify community code |
| GET | `/rides` | List all rides in your community |
| POST | `/rides` | Post a new ride |
| POST | `/rides/{id}/join` | Join a ride |
| DELETE | `/rides/{id}` | Cancel your ride |
| GET | `/leaderboard` | View monthly rankings |
| GET | `/users/me` | View your profile & stats |
| PATCH | `/users/me` | Update your profile |

---

## BIT2083 — SDG 11 Project
**Faculty of Information Technology, City University Malaysia**
