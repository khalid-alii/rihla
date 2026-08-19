from typing import Optional

from pydantic import BaseModel


class CommunityInfo(BaseModel):
    id: str
    name: str


class StatsOut(BaseModel):
    rides_joined: int
    rides_posted: int
    total_rides: int


class UserOut(BaseModel):
    """Full user profile — password_hash is deliberately absent from every field."""

    id: str
    name: str
    email: str
    about: Optional[str] = None
    community: Optional[CommunityInfo] = None
    stats: StatsOut


class PatchUserIn(BaseModel):
    """Only name and about are editable; email/community_id silently ignored."""

    name: Optional[str] = None
    about: Optional[str] = None
