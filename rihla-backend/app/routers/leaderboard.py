import calendar
import re
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import BadRequest, Forbidden
from app.models.ride import Ride
from app.models.ride_join import RideJoin
from app.models.user import User
from app.schemas.leaderboard import LeaderboardOut, RankingEntry, UserRankEntry
from app.schemas.ride import compute_initials

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


@router.get("", response_model=LeaderboardOut)
def get_leaderboard(
    month: Optional[str] = Query(None, description="YYYY-MM — defaults to current UTC month"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LeaderboardOut:
    if not current_user.community_id:
        raise Forbidden("You must verify a community code first.")

    # Validate / default the month parameter.
    if month is not None:
        if not _MONTH_RE.match(month):
            raise BadRequest("month must be in YYYY-MM format.")
        year, mon = int(month[:4]), int(month[5:])
        try:
            date(year, mon, 1)
        except ValueError:
            raise BadRequest("month is not a valid calendar month.")
    else:
        now = datetime.now(timezone.utc)
        year, mon = now.year, now.month
        month = f"{year:04d}-{mon:02d}"

    # Build UTC-aware datetime bounds for the month.
    start_dt = datetime(year, mon, 1, tzinfo=timezone.utc)
    last_day = calendar.monthrange(year, mon)[1]
    end_dt = datetime(year, mon, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    # resets_on = first day of the following month.
    if mon == 12:
        resets_on = date(year + 1, 1, 1).isoformat()
    else:
        resets_on = date(year, mon + 1, 1).isoformat()

    # Ranking metric: count of RideJoin rows where the ride's driver is that user
    # AND joined_at falls in the queried month (§5 leaderboard spec).
    # A ride with 4 riders counts as 4, not 1.
    rows: List = (
        db.query(User, func.count(RideJoin.id).label("riders_taken"))
        .join(Ride, Ride.driver_id == User.id)
        .join(RideJoin, RideJoin.ride_id == Ride.id)
        .filter(
            Ride.community_id == current_user.community_id,
            RideJoin.joined_at >= start_dt,
            RideJoin.joined_at <= end_dt,
        )
        .group_by(User.id)
        .order_by(func.count(RideJoin.id).desc())
        .all()
    )

    rankings = [
        RankingEntry(
            rank=rank,
            user=UserRankEntry(
                id=str(user.id),
                name=user.name,
                initials=compute_initials(user.name),
            ),
            riders_taken=riders_taken,
        )
        for rank, (user, riders_taken) in enumerate(rows, start=1)
    ]

    return LeaderboardOut(month=month, resets_on=resets_on, rankings=rankings)
