import pytest
from pydantic import ValidationError

from aic.public.registration import EarlyAccessRegistration, classify_qualified


def test_registration_with_only_email_is_valid() -> None:
    registration = EarlyAccessRegistration(email="visitor@example.com")

    assert registration.email == "visitor@example.com"
    assert registration.name is None
    assert registration.role is None
    assert registration.qualified is False


def test_registration_rejects_malformed_email() -> None:
    with pytest.raises(ValidationError):
        EarlyAccessRegistration(email="not-an-email")


@pytest.mark.parametrize(
    "role",
    [
        "individual investor",
        "serious retail investor",
        "finance professional",
        "investment professional",
        "Individual Investor",  # case-insensitive
        "  finance professional  ",  # whitespace-tolerant
    ],
)
def test_classify_qualified_matches_target_audience_roles(role: str) -> None:
    assert classify_qualified(role) is True


@pytest.mark.parametrize("role", [None, "", "curious hobbyist", "other"])
def test_classify_qualified_rejects_non_target_audience(role: str | None) -> None:
    assert classify_qualified(role) is False
