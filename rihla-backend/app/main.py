from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routers import auth, community, leaderboard, rides, users

app = FastAPI(
    title="Rihla API",
    description="Community-scoped ride-sharing backend (SDG 11 project).",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers — normalise every error to {"error": "..."} shape
# ---------------------------------------------------------------------------
app.add_exception_handler(AppException, app_exception_handler)          # type: ignore[arg-type]
app.add_exception_handler(HTTPException, http_exception_handler)         # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

# ---------------------------------------------------------------------------
# Routers — no /api prefix; paths are exactly as in the contract
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(community.router)
app.include_router(rides.router)
app.include_router(leaderboard.router)
app.include_router(users.router)


@app.get("/", include_in_schema=False)
def health() -> dict:
    return {"status": "ok", "service": "rihla-api"}
