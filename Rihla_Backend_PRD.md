# Rihla — Backend Build PRD (v1)

**For:** Antigravity (AI coding agent)
**From:** Khalid
**Status:** Final — ready to build
**Stack:** Python, FastAPI, PostgreSQL, JWT auth
**Inputs this PRD is built from:** `Rihla_Backend.pdf` (frontend dev's handoff spec — treat as the source of truth for the API contract) and `rihla_1.html` (the completed frontend prototype)

---

## 1. Context

Rihla is a free, community-scoped ride-sharing web app (SDG 11 project). One user model — anyone can post a ride (as driver) or join one (as rider). Rides are only visible to people in the same community (building/campus/neighborhood), gated by a community code entered once at signup.

The frontend (`rihla_1.html`) is visually and functionally complete but is currently a **static prototype**: all data lives in in-memory JS arrays (`rides`, `board`), and there is no `fetch()` call anywhere in the file. Auth, community-code entry, ride posting, joining, and profile editing are all faked client-side with no persistence.

**Your job:** build the FastAPI + PostgreSQL backend that implements the API contract below exactly, so my frontend collaborator can later swap the mock arrays for `fetch()` calls with zero renegotiation. Field names, casing (snake_case), date format (ISO `YYYY-MM-DD`), and time format (24-hour `HH:MM`) are final — build to match the frontend, not the other way around.

Do not modify `rihla_1.html`. This PRD is backend-only.

---

## 2. Tech stack & project structure

```
rihla-backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router includes, exception handlers
│   ├── config.py                # Settings via pydantic-settings, reads .env
│   ├── database.py              # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── user.py
│   │   ├── community.py
│   │   ├── ride.py
│   │   └── ride_join.py
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── community.py
│   │   ├── ride.py
│   │   ├── leaderboard.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── community.py
│   │   ├── rides.py
│   │   ├── leaderboard.py
│   │   └── users.py
│   ├── auth/
│   │   ├── security.py          # password hashing, JWT encode/decode
│   │   └── dependencies.py      # get_current_user()
│   ├── services/
│   │   └── notifications.py     # email sending abstraction
│   └── exceptions.py             # custom exceptions + {"error": "..."} handler
├── alembic/                      # migrations
├── scripts/
│   └── seed.py                   # creates the RIHLA-2026 community
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

Use SQLAlchemy (sync, `psycopg2-binary`) unless you're already set up for async — sync is simpler to get right for a v1 of this size and the transaction locking in Section 6.4 is easiest to reason about synchronously.

---

## 3. Data models

### User
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK, `default=uuid4` |
| name | string | not null |
| email | string | unique, not null, indexed |
| password_hash | string | bcrypt, never serialized in any response |
| profile_picture_url | string | nullable — not used by the current frontend, keep the column but no upload endpoint in v1 |
| about | string | nullable |
| community_id | FK → Community | nullable |
| created_at | datetime | server default now() |

### Community
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | string | not null |
| code | string | unique, **stored uppercase**, matched case-insensitively on verify |
| active | bool | default true |

### Ride
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| driver_id | FK → User | not null |
| community_id | FK → Community | copied from driver at creation, not re-derived later |
| origin | string | not null |
| destination | string | not null |
| date | date | not null |
| time | time | not null |
| seats_total | int | not null, immutable after creation (Decision 2) |
| seats_available | int | starts equal to seats_total |
| notes | string | nullable |
| status | enum/string | `active` \| `full` \| `cancelled`, default `active` |
| created_at | datetime | server default now() |

### RideJoin
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| ride_id | FK → Ride | not null |
| rider_id | FK → User | not null |
| joined_at | datetime | server default now() |

Add a **unique constraint on `(ride_id, rider_id)`** — this isn't spelled out explicitly in the handoff doc but it's the only way to enforce the documented 409 "You've already joined this ride" behavior at the DB level instead of trusting an application-layer check alone.

Never add counter columns (`rides_joined`, `rides_posted`, etc.) to `User`. Every stat and the leaderboard are always computed live from `Ride` + `RideJoin`, per the handoff doc — this is intentional so nothing can desync.

Use `Enum('active','full','cancelled', name='ride_status')` or a plain `String` with a CHECK constraint — either is fine, just enforce it at the DB level, not only in Pydantic.

---

## 4. Auth

- Bearer JWT on every endpoint except `POST /auth/register` and `POST /auth/login`.
- Token payload: `{"sub": user_id, "exp": ...}`. Use a 30-day expiry — the contract doesn't define a refresh-token flow, so keep v1 simple with one long-lived token rather than inventing a refresh mechanism that isn't in the spec.
- `get_current_user()` dependency: decode token → 401 if invalid/expired → load user from DB → 401 if user no longer exists.
- **Never trust a `user_id` in a request body.** Every endpoint that needs "who is doing this" (posting a ride, joining, cancelling, editing profile) resolves it from the token, full stop.
- Passwords: bcrypt via `passlib`. `password_hash` must never appear in any serialized response — enforce this at the Pydantic response-model level (a `UserOut` schema that simply doesn't have the field), not by remembering to strip it manually in each route.

---

## 5. Endpoints

All paths are root-level, no `/api` prefix — match the contract exactly as the frontend will be wired to these exact paths.

### `POST /auth/register`
**Body:** `{ "name": str, "email": str, "password": str }`
**201:** `{ "token": str, "user": { "id", "name", "community_id" } }`
- `community_id` is `null` for every new registration (community assignment only happens via `/community/verify`).
- 409 if email already registered.

### `POST /auth/login`
**Body:** `{ "email": str, "password": str }`
**200:** `{ "token": str, "user": { "id", "name", "community_id" } }`
- ⚠️ Implementation note: the handoff doc's example response shows `"community_id": null` — that's just because the example user hasn't onboarded yet. On a real login, `community_id` must reflect the **actual current value** on that user's row (which will be non-null for anyone who already completed community verification in a previous session). This is what lets the frontend decide whether to route to the community-code screen or straight to Home.
- 401 on bad credentials — don't leak whether it was the email or password that was wrong.

### `POST /community/verify`
**Body:** `{ "code": str }`
**200:** `{ "community": { "id", "name" } }` — also sets `current_user.community_id` on success.
**400:** `{ "error": "That code doesn't match a community. Check with your building or campus admin." }` — same message for "code doesn't exist" and "code exists but `active=false`"; don't distinguish, it's not meaningful to the end user and it avoids leaking which codes exist.
- Match case-insensitively (uppercase the input, compare against the stored uppercase code).

### `GET /rides`
**200:** array of ride objects, scoped to `current_user.community_id`, `status in (active, full)` only (cancelled rides never appear), ordered soonest-first by `(date, time)` ascending.
```json
{
  "id": "r_101",
  "driver": { "id": "u_4", "name": "Diego Fernandez", "initials": "DF" },
  "origin": "Maple Court",
  "destination": "Downtown Station",
  "date": "2026-08-19",
  "time": "18:40",
  "seats_total": 3,
  "seats_available": 3,
  "notes": "Leaving right after work, happy to wait 5 min.",
  "status": "active"
}
```
- `initials` is **computed server-side** from the driver's `name` (first letter of first + last word, uppercased — e.g. "Diego Fernandez" → "DF"). This isn't stored; derive it in the serializer.
- Empty community → `[]`. No special "empty" flag — the frontend's empty-state already renders off a plain empty array.
- If `current_user.community_id` is `null` (hasn't verified a code yet), return `403` — this state shouldn't be reachable from the frontend flow, but the backend shouldn't assume the frontend enforces it.

### `POST /rides`
**Body:** `{ "origin", "destination", "date", "time", "seats_total", "notes"? }`
**201:** same shape as a `GET /rides` item.
- `driver_id` = current user, `community_id` = current user's community (copied at creation, per Decision).
- `seats_available` initialized to `seats_total`.
- Validate `seats_total >= 1`.

### `DELETE /rides/{id}`
**204**, no body.
- 403 if `current_user.id != ride.driver_id`.
- Sets `status = cancelled` (soft delete — row stays).
- Fires an email to every rider on that ride (see Section 6).
- 404 if the ride doesn't exist or already belongs to a different community than the requester (don't leak existence across communities).

### `POST /rides/{id}/join`
**200:** `{ "id", "seats_available", "status" }`
**409** `{ "error": "This ride is full." }`
**409** `{ "error": "You've already joined this ride." }`
**403** `{ "error": "You can't join your own ride." }`

This is the one endpoint with a real concurrency requirement — see Section 6.4 for the exact transaction shape.

### `GET /leaderboard?month=YYYY-MM`
**200:**
```json
{
  "month": "2026-08",
  "resets_on": "2026-09-01",
  "rankings": [
    { "rank": 1, "user": { "id", "name", "initials" }, "riders_taken": 19 }
  ]
}
```
- Defaults to current month (server clock — use UTC consistently) if `month` omitted.
- Community-scoped to `current_user.community_id`.
- Ranking metric: **count of `RideJoin` rows** where the ride's `driver_id` is that user and `joined_at` falls in the given month — a ride with 4 riders counts as 4, not 1. This is a live query against `RideJoin` + `Ride`, not a stored score — no cron job.
- `resets_on` = first day of the month *after* the queried month, ISO date.
- Validate `month` matches `YYYY-MM`; 400 on malformed input.

### `GET /users/me`
**200:**
```json
{
  "id", "name", "email", "about",
  "community": { "id", "name" },
  "stats": { "rides_joined": int, "rides_posted": int, "total_rides": int }
}
```
- `total_rides = rides_joined + rides_posted`.
- ⚠️ Decision (not specified in the handoff doc — flagging so you don't have to guess): count **all** rows regardless of ride status, including cancelled rides, for both `rides_joined` and `rides_posted`. This mirrors the leaderboard query, which also doesn't filter out cancelled rides — keeping the same rule in both places avoids the profile stats and leaderboard numbers silently disagreeing with each other.

### `PATCH /users/me`
**Body:** any subset of `{ "name", "about" }`.
**200:** full updated user object, same shape as `GET /users/me`.
- `email` and `community_id` are **not** editable through this endpoint — if either key is present in the body, ignore it silently rather than erroring (matches the frontend, which only ever shows `name` and `about` as editable fields; `email` is rendered but disabled).

---

## 6. Business logic details

### 6.1 Error shape
Every documented error response is `{ "error": "human-readable message" }`. FastAPI's default validation-error body (`{"detail": [...]}`) does **not** match this — add a global exception handler in `main.py` that normalizes `RequestValidationError` and your own custom exceptions into the `{"error": ...}` shape, so the contract holds even on inputs the spec didn't explicitly enumerate.

### 6.2 Community code matching
Store `code` uppercase. On verify, `.strip().upper()` the input before comparing. Reject if `active = false` with the same error message as "not found."

### 6.3 Cancellation → notification
On `DELETE /rides/{id}`, after setting `status = cancelled`, look up every `RideJoin` on that ride and send one email per rider:
- Subject: `Your ride to {destination} was cancelled`
- Body: names the driver, date, and time.

Build this as a small `notifications.py` service with a single `send_email(to, subject, body)` function, configured via env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). If those env vars aren't set, log the email to stdout instead of raising — this is a student project and you shouldn't need real SMTP credentials configured just to run and demo the app locally. This is the only notification in v1 — no push, no in-app inbox.

### 6.4 Seat booking — the one real concurrency risk
Two riders can hit "Join ride" on the same last seat at nearly the same instant. Handle it with a row lock inside a transaction:

```python
with db.begin():
    ride = db.query(Ride).filter(Ride.id == ride_id).with_for_update().one_or_none()
    if ride is None or ride.community_id != current_user.community_id:
        raise NotFound()
    if ride.driver_id == current_user.id:
        raise Forbidden("You can't join your own ride.")
    if ride.status == "cancelled" or ride.seats_available <= 0:
        raise Conflict("This ride is full.")
    already = db.query(RideJoin).filter_by(ride_id=ride.id, rider_id=current_user.id).first()
    if already:
        raise Conflict("You've already joined this ride.")

    db.add(RideJoin(ride_id=ride.id, rider_id=current_user.id))
    ride.seats_available -= 1
    if ride.seats_available == 0:
        ride.status = "full"
    db.flush()
```

`with_for_update()` (`SELECT ... FOR UPDATE`) is what prevents two concurrent requests from both reading `seats_available = 1` and both decrementing successfully.

### 6.5 Ordering & sorting
`GET /rides` sorts by `(date, time)` ascending. Combine both columns for the `ORDER BY` — don't sort by `date` alone and leave `time` unordered within a day.

---

## 7. Seed data

The frontend prototype hard-codes the community code `RIHLA-2026` (see `verifyCode()` in `rihla_1.html`) and displays "Cedar Heights Campus" as the community name. Seed exactly this so the prototype keeps working once wired up:

```python
# scripts/seed.py
Community(name="City University Cyberjaya Campus", code="CITYU-2026", active=True)
```

Run this once against a fresh DB (via `python -m scripts.seed` or as an Alembic data migration — either is fine).

---

## 8. CORS & frontend integration

- Enable CORS for whatever origin `rihla_1.html` is served from during development (e.g. a local static server on `http://127.0.0.1:5500` or similar — adjust to match however your collaborator runs it) plus the eventual production origin.
- No API versioning prefix — endpoints are exactly `/auth/register`, `/rides`, `/leaderboard`, etc., at root, matching the contract as written.
- The frontend currently displays combined strings like `"Today · 6:40 PM"` and computes driver initials in its own mock-data JS — **don't replicate that formatting on the backend.** Keep returning separate `date` (`YYYY-MM-DD`) and `time` (24-hour `HH:MM`) fields exactly as specified; any "Today/Tomorrow" relative-day labeling and locale/12-hour formatting is frontend presentation logic to be added when the mock arrays get replaced with real `fetch()` calls. Do compute `initials` server-side as specified in Section 5, since the contract puts it in the API response itself, not the frontend.

---

## 9. Non-functional requirements

- PostgreSQL via SQLAlchemy + Alembic migrations (don't hand-write schema — generate and commit migrations).
- `password_hash` never serialized in any response, ever.
- JWT secret read from `JWT_SECRET` env var — never hardcoded, never committed.
- All list/detail endpoints that touch rides are scoped to `current_user.community_id` — there should be no code path where a user from Community A can see or join a ride from Community B, even by guessing a ride ID.
- Interactive API docs available at `/docs` (FastAPI default) — useful for manually verifying the contract against Section 5 before the frontend integration happens.

---

## 10. Environment variables (`.env.example`)

```
DATABASE_URL=postgresql://user:password@localhost:5432/rihla
JWT_SECRET=change-me
JWT_EXPIRY_DAYS=30
CORS_ORIGINS=http://127.0.0.1:5500
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@rihla.app
```

Leave the `SMTP_*` values blank in local dev — per Section 6.3, the notification service should fall back to console logging when they're unset.

---

## 11. Out of scope for v1

(carried over from the handoff spec — don't build any of this)
- No map view / geolocation.
- No in-app messaging between driver and rider.
- No payments — the app is free.
- No moderation/reporting/blocking (the community code is the only trust boundary in v1).
- No editing `seats_total` after a ride is posted — cancel and repost instead.
- No push notifications or in-app inbox — email only, and only for cancellations.
- No refresh-token flow — one long-lived JWT per login.

---

## 12. Definition of done

- All 10 endpoints in Section 5 implemented and matching the contract exactly: paths, field names, casing, status codes, and error message strings.
- `/docs` loads and every endpoint is manually exercisable there.
- Seed script produces the `RIHLA-2026` / "Cedar Heights Campus" community.
- Two concurrent `POST /rides/{id}/join` requests against a ride with 1 seat left: exactly one succeeds with 200, the other gets 409 — never both succeeding.
- Cancelling a ride with active riders either sends real emails (if SMTP env vars are set) or logs them to stdout (if not) — it should never crash either way.
- No `password_hash` field appears in any response body, checked by inspection of the response schemas, not just by testing happy paths.
