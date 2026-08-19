import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        # Enforce status at DB level — Pydantic alone isn't enough.
        CheckConstraint(
            "status IN ('active', 'full', 'cancelled')",
            name="ck_ride_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # community_id is copied from driver at creation and never re-derived.
    community_id = Column(UUID(as_uuid=True), ForeignKey("communities.id"), nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    seats_total = Column(Integer, nullable=False)
    # seats_available starts equal to seats_total; decremented on join.
    seats_available = Column(Integer, nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    driver = relationship("User", back_populates="rides", foreign_keys=[driver_id])
    community = relationship("Community")
    joins = relationship("RideJoin", back_populates="ride")
