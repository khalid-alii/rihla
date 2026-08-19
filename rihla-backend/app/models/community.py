import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Community(Base):
    __tablename__ = "communities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    # Stored uppercase; matched case-insensitively on verify (§6.2).
    code = Column(String, unique=True, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
