from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

_TARGET_AUDIENCE_ROLES = {
    "individual investor",
    "serious retail investor",
    "finance professional",
    "investment professional",
    "analyst / researcher",
}


def classify_qualified(role: str | None) -> bool:
    """A registration is "qualified" for the qualified-interest rate when the
    visitor selected a role/investor-profile value matching the stated target
    audience, rather than leaving it blank or selecting an out-of-audience value.
    A simple, adjustable heuristic (spec Assumptions), not a hard business rule."""
    if role is None:
        return False
    return role.strip().lower() in _TARGET_AUDIENCE_ROLES


class EarlyAccessRegistration(BaseModel):
    registration_id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    name: str | None = None
    role: str | None = None
    experience: str | None = None
    interests: str | None = None
    feedback: str | None = None
    qualified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
