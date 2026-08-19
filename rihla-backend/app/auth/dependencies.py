from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database import get_db
from app.exceptions import Unauthorized
from app.models.user import User


class _JWTBearer(HTTPBearer):
    """HTTPBearer subclass that converts missing/malformed Authorization headers
    into a 401 Unauthorized instead of FastAPI's default 403."""

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise Unauthorized("Authentication required.")


_bearer = _JWTBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: decode JWT → load User → 401 on any failure.

    Caller should never trust a user_id in the request body — always use this.
    """
    token = credentials.credentials
    try:
        user_id = decode_token(token)
    except JWTError:
        raise Unauthorized("Invalid or expired token.")

    user: Optional[User] = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise Unauthorized("User no longer exists.")

    return user
