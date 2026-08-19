"""Package init — importing all models here ensures they are registered
with SQLAlchemy's Base metadata so Alembic can discover them."""

from app.models.community import Community  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.ride import Ride  # noqa: F401
from app.models.ride_join import RideJoin  # noqa: F401
