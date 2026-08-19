import uuid
from datetime import date, time
from typing import List

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session, joinedload

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import Conflict, Forbidden, NotFound
from app.models.ride import Ride
from app.models.ride_join import RideJoin
from app.models.user import User
from app.schemas.ride import DriverOut, JoinOut, RideIn, RideOut, compute_initials
from app.services.notifications import send_email

router = APIRouter(prefix="/rides", tags=["rides"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_ride_out(ride: Ride) -> RideOut:
    """Convert a Ride ORM object (with .driver loaded) to RideOut."""
    return RideOut(
        id=str(ride.id),
        driver=DriverOut(
            id=str(ride.driver.id),
            name=ride.driver.name,
            initials=compute_initials(ride.driver.name),
        ),
        origin=ride.origin,
        destination=ride.destination,
        date=ride.date.isoformat(),          # YYYY-MM-DD
        time=ride.time.strftime("%H:%M"),    # HH:MM 24-hour
        seats_total=ride.seats_total,
        seats_available=ride.seats_available,
        notes=ride.notes,
        status=ride.status,
    )


def _load_ride_with_driver(db: Session, ride_id: uuid.UUID) -> Ride:
    return (
        db.query(Ride)
        .options(joinedload(Ride.driver))
        .filter(Ride.id == ride_id)
        .one()
    )


# ---------------------------------------------------------------------------
# GET /rides
# ---------------------------------------------------------------------------

@router.get("", response_model=List[RideOut])
def list_rides(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RideOut]:
    if not current_user.community_id:
        raise Forbidden("You must verify a community code before viewing rides.")

    rides = (
        db.query(Ride)
        .options(joinedload(Ride.driver))
        .filter(
            Ride.community_id == current_user.community_id,
            Ride.status.in_(["active", "full"]),
        )
        .order_by(Ride.date.asc(), Ride.time.asc())
        .all()
    )
    return [_build_ride_out(r) for r in rides]


# ---------------------------------------------------------------------------
# POST /rides
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=RideOut)
def create_ride(
    body: RideIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RideOut:
    if not current_user.community_id:
        raise Forbidden("You must verify a community code before posting a ride.")

    ride = Ride(
        driver_id=current_user.id,
        community_id=current_user.community_id,
        origin=body.origin,
        destination=body.destination,
        date=date.fromisoformat(body.date),
        time=time.fromisoformat(body.time),
        seats_total=body.seats_total,
        seats_available=body.seats_total,
        notes=body.notes,
        status="active",
    )
    db.add(ride)
    db.commit()

    # Re-query to eagerly load driver relationship before serializing.
    ride = _load_ride_with_driver(db, ride.id)
    return _build_ride_out(ride)


# ---------------------------------------------------------------------------
# DELETE /rides/{id}  — soft cancel
# ---------------------------------------------------------------------------

@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        rid = uuid.UUID(ride_id)
    except ValueError:
        raise NotFound()

    # Load ride + joins + each rider's email in one query.
    ride = (
        db.query(Ride)
        .options(joinedload(Ride.joins).joinedload(RideJoin.rider))
        .filter(Ride.id == rid)
        .first()
    )

    # 404 if not found OR belongs to a different community (don't leak existence).
    if ride is None or ride.community_id != current_user.community_id:
        raise NotFound()

    # 403 if requester is not the driver.
    if ride.driver_id != current_user.id:
        raise Forbidden("You are not the driver of this ride.")

    if ride.status == "cancelled":
        # Already cancelled — idempotent, no extra emails.
        return

    # Capture rider data before commit so we can email after.
    riders = [
        (join.rider.email, join.rider.name)
        for join in ride.joins
        if join.rider is not None
    ]
    ride_dest = ride.destination
    ride_date = ride.date.isoformat()
    ride_time = ride.time.strftime("%H:%M")
    driver_name = current_user.name

    ride.status = "cancelled"
    db.commit()

    # Send cancellation emails — never raises (falls back to stdout).
    for rider_email, rider_name in riders:
        send_email(
            to=rider_email,
            subject=f"Your ride to {ride_dest} was cancelled",
            body=(
                f"Hi {rider_name},\n\n"
                f"Your upcoming ride with {driver_name} to {ride_dest} "
                f"on {ride_date} at {ride_time} has been cancelled by the driver.\n\n"
                f"We're sorry for the inconvenience. Check Rihla for other available rides.\n\n"
                f"— The Rihla Team"
            ),
        )


# ---------------------------------------------------------------------------
# POST /rides/{id}/join  — the one endpoint with real concurrency risk (§6.4)
# ---------------------------------------------------------------------------

@router.post("/{ride_id}/join", response_model=JoinOut)
def join_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JoinOut:
    try:
        rid = uuid.UUID(ride_id)
    except ValueError:
        raise NotFound()

    # SELECT ... FOR UPDATE locks this row until we commit, preventing two
    # concurrent requests from both seeing seats_available > 0 on the last seat.
    ride = (
        db.query(Ride)
        .filter(Ride.id == rid)
        .with_for_update()
        .one_or_none()
    )

    if ride is None or ride.community_id != current_user.community_id:
        raise NotFound()

    if ride.driver_id == current_user.id:
        raise Forbidden("You can't join your own ride.")

    if ride.status == "cancelled" or ride.seats_available <= 0:
        raise Conflict("This ride is full.")

    already = (
        db.query(RideJoin)
        .filter(RideJoin.ride_id == ride.id, RideJoin.rider_id == current_user.id)
        .first()
    )
    if already:
        raise Conflict("You've already joined this ride.")

    db.add(RideJoin(ride_id=ride.id, rider_id=current_user.id))
    ride.seats_available -= 1
    if ride.seats_available == 0:
        ride.status = "full"

    try:
        db.flush()   # Surface DB-level unique constraint before commit.
        db.commit()
    except sa_exc.IntegrityError:
        db.rollback()
        raise Conflict("You've already joined this ride.")

    return JoinOut(
        id=str(ride.id),
        seats_available=ride.seats_available,
        status=ride.status,
    )
