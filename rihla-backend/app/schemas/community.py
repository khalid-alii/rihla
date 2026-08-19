from pydantic import BaseModel


class VerifyIn(BaseModel):
    code: str


class CommunityOut(BaseModel):
    id: str
    name: str


class CommunityVerifyOut(BaseModel):
    community: CommunityOut
