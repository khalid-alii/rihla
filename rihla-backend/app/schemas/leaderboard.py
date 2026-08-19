from typing import List

from pydantic import BaseModel


class UserRankEntry(BaseModel):
    id: str
    name: str
    initials: str


class RankingEntry(BaseModel):
    rank: int
    user: UserRankEntry
    riders_taken: int


class LeaderboardOut(BaseModel):
    month: str          # YYYY-MM
    resets_on: str      # YYYY-MM-DD (first day of next month)
    rankings: List[RankingEntry]
