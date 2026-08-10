from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from aic.domain import FinancialSnapshot, Money


def test_valid_construction_with_partial_metrics() -> None:
    snapshot = FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
    )
    assert snapshot.revenue is not None
    assert snapshot.revenue.amount == Decimal(6500000000)
    assert snapshot.free_cash_flow is None
    assert snapshot.shares_outstanding is None


def test_all_metrics_optional() -> None:
    snapshot = FinancialSnapshot(as_of=date(2026, 3, 31))
    assert snapshot.revenue is None
    assert snapshot.operating_income is None
    assert snapshot.net_income is None
    assert snapshot.free_cash_flow is None
    assert snapshot.cash is None
    assert snapshot.debt is None
    assert snapshot.shares_outstanding is None


def test_required_field_validation() -> None:
    with pytest.raises(ValidationError):
        FinancialSnapshot()


def test_rejects_monetary_metric_with_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        FinancialSnapshot(
            as_of=date(2026, 3, 31),
            revenue=Money(amount=Decimal(1), currency="NOTREAL"),
        )


def test_rejects_mixed_currencies_across_metrics() -> None:
    with pytest.raises(ValidationError):
        FinancialSnapshot(
            as_of=date(2026, 3, 31),
            revenue=Money(amount=Decimal(100), currency="EUR"),
            cash=Money(amount=Decimal(50), currency="USD"),
        )


def test_round_trip_serialization() -> None:
    snapshot = FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
        shares_outstanding=Decimal(400000000),
    )
    restored = FinancialSnapshot.model_validate(snapshot.model_dump())
    assert restored == snapshot
