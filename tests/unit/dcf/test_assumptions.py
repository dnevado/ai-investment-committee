from decimal import Decimal

import pytest
from pydantic import ValidationError

from aic.dcf import DCFAssumptions, ForecastYear
from aic.domain import Money


def _money(amount: str, currency: str = "USD") -> Money:
    return Money(amount=Decimal(amount), currency=currency)


def _valid_kwargs() -> dict:
    return {
        "forecast": [
            ForecastYear(
                revenue=_money("1000"),
                depreciation_and_amortization=_money("50"),
                capital_expenditure=_money("60"),
                change_in_net_working_capital=_money("10"),
            )
        ],
        "operating_margin": Decimal("0.20"),
        "tax_rate": Decimal("0.25"),
        "wacc": Decimal("0.10"),
        "terminal_growth_rate": Decimal("0.02"),
        "cash": _money("200"),
        "debt": _money("150"),
        "shares_outstanding": Decimal(100),
    }


def test_valid_construction() -> None:
    assumptions = DCFAssumptions(**_valid_kwargs())
    assert assumptions.wacc == Decimal("0.10")


def test_rejects_wacc_equal_to_terminal_growth() -> None:
    kwargs = _valid_kwargs()
    kwargs["wacc"] = Decimal("0.05")
    kwargs["terminal_growth_rate"] = Decimal("0.05")
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


def test_rejects_wacc_below_terminal_growth() -> None:
    kwargs = _valid_kwargs()
    kwargs["wacc"] = Decimal("0.02")
    kwargs["terminal_growth_rate"] = Decimal("0.05")
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


@pytest.mark.parametrize("wacc", [Decimal(0), Decimal("-0.01")])
def test_rejects_non_positive_wacc(wacc: Decimal) -> None:
    kwargs = _valid_kwargs()
    kwargs["wacc"] = wacc
    kwargs["terminal_growth_rate"] = Decimal(-1)
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


def test_rejects_empty_forecast() -> None:
    kwargs = _valid_kwargs()
    kwargs["forecast"] = []
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


@pytest.mark.parametrize("shares", [Decimal(0), Decimal(-1)])
def test_rejects_non_positive_shares_outstanding(shares: Decimal) -> None:
    kwargs = _valid_kwargs()
    kwargs["shares_outstanding"] = shares
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


@pytest.mark.parametrize("tax_rate", [Decimal("-0.01"), Decimal("1.01")])
def test_rejects_tax_rate_outside_bounds(tax_rate: Decimal) -> None:
    kwargs = _valid_kwargs()
    kwargs["tax_rate"] = tax_rate
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


@pytest.mark.parametrize(
    "missing_field",
    [
        "forecast",
        "operating_margin",
        "tax_rate",
        "wacc",
        "terminal_growth_rate",
        "cash",
        "debt",
        "shares_outstanding",
    ],
)
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)


def test_rejects_mismatched_currency() -> None:
    kwargs = _valid_kwargs()
    kwargs["debt"] = _money("150", "EUR")
    with pytest.raises(ValidationError):
        DCFAssumptions(**kwargs)
