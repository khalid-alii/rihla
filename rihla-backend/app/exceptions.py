from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class AppException(Exception):
    """Base for all application-level errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class BadRequest(AppException):
    def __init__(self, message: str = "Bad request.") -> None:
        super().__init__(400, message)


class Unauthorized(AppException):
    def __init__(self, message: str = "Unauthorized.") -> None:
        super().__init__(401, message)


class Forbidden(AppException):
    def __init__(self, message: str = "Forbidden.") -> None:
        super().__init__(403, message)


class NotFound(AppException):
    def __init__(self, message: str = "Not found.") -> None:
        super().__init__(404, message)


class Conflict(AppException):
    def __init__(self, message: str = "Conflict.") -> None:
        super().__init__(409, message)


# ---------------------------------------------------------------------------
# Exception handlers (registered in main.py)
# ---------------------------------------------------------------------------

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize FastAPI's own HTTPException into {"error": ...} shape."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        message = exc.detail["error"]
    else:
        message = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": message})


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return the first Pydantic validation message in {"error": ...} shape."""
    errors = exc.errors()
    message = errors[0].get("msg", "Validation error.") if errors else "Validation error."
    return JSONResponse(status_code=422, content={"error": message})
