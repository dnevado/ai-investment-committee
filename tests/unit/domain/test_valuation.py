import types
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import Money, ValuationResult


def _valid_kwargs() -> dict:
    return {
        "valuation_id": uuid4(),
        "method": "comparable-multiples (placeholder)",
        "valuation_date": date(2026, 8, 10),
        "estimated_value": Money(amount=Decimal("850.00"), currency="EUR"),
        "confidence": 0.6,
        "assumption_evidence_refs": [uuid4()],
    }


def test_valid_construction_with_money() -> None:
    valuation = ValuationResult(**_valid_kwargs())
    assert isinstance(valuation.estimated_value, Money)
    assert valuation.estimated_value.amount == Decimal("850.00")
    assert valuation.estimated_value.currency == "EUR"


@pytest.mark.parametrize(
    "missing_field",
    ["valuation_id", "method", "valuation_date", "estimated_value", "confidence"],
)
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        ValuationResult(**kwargs)


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_accepts_confidence_within_bounds(confidence: float) -> None:
    kwargs = _valid_kwargs()
    kwargs["confidence"] = confidence
    valuation = ValuationResult(**kwargs)
    assert valuation.confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_rejects_confidence_outside_bounds(confidence: float) -> None:
    kwargs = _valid_kwargs()
    kwargs["confidence"] = confidence
    with pytest.raises(ValidationError):
        ValuationResult(**kwargs)


def test_rejects_estimated_value_with_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        Money(amount=Decimal(1), currency="NOTREAL")


def test_no_calculation_behavior() -> None:
    custom_methods = [
        name
        for name, value in vars(ValuationResult).items()
        if isinstance(value, types.FunctionType)
    ]
    assert custom_methods == []


def test_round_trip_serialization() -> None:
    valuation = ValuationResult(**_valid_kwargs())
    restored = ValuationResult.model_validate(valuation.model_dump())
    assert restored == valuation
