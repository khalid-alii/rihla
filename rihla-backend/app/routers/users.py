from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.ride import Ride
from app.models.ride_join import RideJoin
from app.models.user import User
from app.schemas.user import CommunityInfo, PatchUserIn, StatsOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _build_user_out(user: User, db: Session) -> UserOut:
    """Build the full UserOut response, computing live stats from DB."""
    # Count all rides posted — all statuses, including cancelled (§5 /users/me note).
    rides_posted: int = (
        db.query(func.count(Ride.id)).filter(Ride.driver_id == user.id).scalar() or 0
    )
    # Count all joins — all statuses, including rides later cancelled.
    rides_joined: int = (
        db.query(func.count(RideJoin.id))
        .filter(RideJoin.rider_id == user.id)
        .scalar()
        or 0
    )

    community_info: CommunityInfo | None = None
    if user.community_id and user.community:
        community_info = CommunityInfo(
            id=str(user.community.id),
            name=user.community.name,
        )

    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        about=user.about,
        community=community_info,
        stats=StatsOut(
            rides_joined=rides_joined,
            rides_posted=rides_posted,
            total_rides=rides_joined + rides_posted,
        ),
    )


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserOut)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    # Eagerly load community so _build_user_out can access it.
    user = (
        db.query(User)
        .options(joinedload(User.community))
        .filter(User.id == current_user.id)
        .one()
    )
    return _build_user_out(user, db)


# ---------------------------------------------------------------------------
# PATCH /users/me
# ---------------------------------------------------------------------------

@router.patch("/me", response_model=UserOut)
def patch_me(
    body: PatchUserIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    # Only name and about are editable; email/community_id silently ignored.
    if body.name is not None:
        current_user.name = body.name
    if body.about is not None:
        current_user.about = body.about

    db.commit()

    # Re-load with community eager-loaded for the response.
    user = (
        db.query(User)
        .options(joinedload(User.community))
        .filter(User.id == current_user.id)
        .one()
    )
    return _build_user_out(user, db)
