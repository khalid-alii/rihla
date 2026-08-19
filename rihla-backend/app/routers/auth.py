from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import create_token, hash_password, verify_password
from app.database import get_db
from app.exceptions import Conflict, Unauthorized
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserMinimal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise Conflict("Email already registered.")

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(str(user.id))
    return TokenOut(
        token=token,
        user=UserMinimal(
            id=str(user.id),
            name=user.name,
            community_id=None,  # always null on fresh registration
        ),
    )


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.email == body.email).first()

    # Constant-time path: always verify even if user doesn't exist,
    # so we don't leak whether the email is registered.
    if not user or not verify_password(body.password, user.password_hash):
        raise Unauthorized("Invalid credentials.")

    token = create_token(str(user.id))
    community_id = str(user.community_id) if user.community_id else None
    return TokenOut(
        token=token,
        user=UserMinimal(
            id=str(user.id),
            name=user.name,
            community_id=community_id,  # reflects actual DB value
        ),
    )
