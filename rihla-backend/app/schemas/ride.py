from typing import Optional

from pydantic import BaseModel, field_validator


def compute_initials(name: str) -> str:
    """First letter of first word + first letter of last word, uppercased.

    Examples:
        "Diego Fernandez" -> "DF"
        "Alice"           -> "A"
        "Mary Jane Watson" -> "MW"
    """
    parts = name.strip().split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class DriverOut(BaseModel):
    id: str
    name: str
    initials: str


class RideIn(BaseModel):
    origin: str
    destination: str
    date: str  # YYYY-MM-DD — kept as str to pass through; validated by DB
    time: str  # HH:MM 24-hour
    seats_total: int
    notes: Optional[str] = None

    @field_validator("seats_total")
    @classmethod
    def seats_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("seats_total must be at least 1.")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date must be YYYY-MM-DD.")
        return v

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("time must be HH:MM (24-hour).")
        return v


class RideOut(BaseModel):
    id: str
    driver: DriverOut
    origin: str
    destination: str
    date: str   # YYYY-MM-DD
    time: str   # HH:MM 24-hour
    seats_total: int
    seats_available: int
    notes: Optional[str] = None
    status: str


class JoinOut(BaseModel):
    id: str
    seats_available: int
    status: str
