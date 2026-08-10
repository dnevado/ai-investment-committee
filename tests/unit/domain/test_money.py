from decimal import Decimal

import pytest
from pydantic import ValidationError

from aic.domain import Money


def test_valid_construction() -> None:
    money = Money(amount=Decimal("850.00"), currency="EUR")
    assert money.amount == Decimal("850.00")
    assert money.currency == "EUR"


def test_rejects_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        Money(amount=Decimal(1), currency="NOTREAL")


def test_round_trip_serialization() -> None:
    money = Money(amount=Decimal("850.00"), currency="EUR")
    restored = Money.model_validate(money.model_dump())
    assert restored == money
