import uuid

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RideJoin(Base):
    __tablename__ = "ride_joins"
    __table_args__ = (
        # DB-level guard against duplicate joins — backs up the application-layer 409.
        UniqueConstraint("ride_id", "rider_id", name="uq_ride_rider"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ride = relationship("Ride", back_populates="joins")
    rider = relationship("User", back_populates="ride_joins")
