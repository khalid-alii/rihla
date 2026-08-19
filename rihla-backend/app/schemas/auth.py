from typing import Optional

from pydantic import BaseModel


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class UserMinimal(BaseModel):
    id: str
    name: str
    community_id: Optional[str] = None


class TokenOut(BaseModel):
    token: str
    user: UserMinimal
