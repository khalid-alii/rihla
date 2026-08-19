import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    # bcrypt hash — never serialised in any response schema.
    password_hash = Column(String, nullable=False)
    profile_picture_url = Column(String, nullable=True)
    about = Column(String, nullable=True)
    community_id = Column(UUID(as_uuid=True), ForeignKey("communities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    community = relationship("Community", lazy="select")
    rides = relationship(
        "Ride",
        back_populates="driver",
        foreign_keys="Ride.driver_id",
    )
    ride_joins = relationship("RideJoin", back_populates="rider")
