from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf, to_valuation_result
from aic.dcf.engine import _round_money
from aic.domain import Money


def _money(amount: str, currency: str = "USD") -> Money:
    return Money(amount=Decimal(amount), currency=currency)


def _simple_assumptions(currency: str = "USD") -> DCFAssumptions:
    return DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=_money("1000", currency),
                depreciation_and_amortization=_money("0", currency),
                capital_expenditure=_money("0", currency),
                change_in_net_working_capital=_money("0", currency),
            )
        ],
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal(0),
        cash=_money("0", currency),
        debt=_money("0", currency),
        shares_outstanding=Decimal(10),
    )


def test_valid_computation_matches_hand_worked_formulas() -> None:
    result = compute_dcf(_simple_assumptions())

    assert len(result.per_year) == 1
    year = result.per_year[0]
    assert year.year == 1
    assert year.fcff.amount == Decimal("500.00")
    assert year.pv_fcff.amount == Decimal("454.55")

    assert result.terminal_value.amount == Decimal("5000.00")
    assert result.pv_terminal_value.amount == Decimal("4545.45")
    assert result.enterprise_value.amount == Decimal("5000.00")
    assert result.equity_value.amount == Decimal("5000.00")
    assert result.implied_value_per_share.amount == Decimal("500.00")


def test_deterministic_output() -> None:
    assumptions = _simple_assumptions()
    first = compute_dcf(assumptions)
    second = compute_dcf(assumptions)
    assert first == second


def test_output_currency_matches_input_currency() -> None:
    result = compute_dcf(_simple_assumptions(currency="EUR"))

    assert result.per_year[0].fcff.currency == "EUR"
    assert result.per_year[0].pv_fcff.currency == "EUR"
    assert result.terminal_value.currency == "EUR"
    assert result.pv_terminal_value.currency == "EUR"
    assert result.enterprise_value.currency == "EUR"
    assert result.equity_value.currency == "EUR"
    assert result.implied_value_per_share.currency == "EUR"


def test_to_valuation_result_maps_implied_value_per_share() -> None:
    result = compute_dcf(_simple_assumptions())
    valuation_id = uuid4()

    valuation_result = to_valuation_result(
        result,
        valuation_id=valuation_id,
        valuation_date=date(2026, 8, 10),
        confidence=0.6,
    )

    assert valuation_result.valuation_id == valuation_id
    assert valuation_result.method == "DCF (FCFF)"
    assert valuation_result.estimated_value == result.implied_value_per_share


def test_reference_case() -> None:
    """Matches spec.md's documented Reference Case exactly (User Story 3)."""
    assumptions = DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=_money("1000.00"),
                depreciation_and_amortization=_money("50.00"),
                capital_expenditure=_money("60.00"),
                change_in_net_working_capital=_money("10.00"),
            ),
            ForecastYear(
                revenue=_money("1100.00"),
                depreciation_and_amortization=_money("50.00"),
                capital_expenditure=_money("60.00"),
                change_in_net_working_capital=_money("10.00"),
            ),
            ForecastYear(
                revenue=_money("1210.00"),
                depreciation_and_amortization=_money("50.00"),
                capital_expenditure=_money("60.00"),
                change_in_net_working_capital=_money("10.00"),
            ),
        ],
        operating_margin=Decimal("0.20"),
        tax_rate=Decimal("0.25"),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal("0.02"),
        cash=_money("200.00"),
        debt=_money("150.00"),
        shares_outstanding=Decimal(100),
    )

    result = compute_dcf(assumptions)

    expected_fcff = [Decimal("130.00"), Decimal("145.00"), Decimal("161.50")]
    expected_pv_fcff = [Decimal("118.18"), Decimal("119.83"), Decimal("121.34")]
    for index, year_result in enumerate(result.per_year):
        assert year_result.year == index + 1
        assert year_result.fcff.amount == expected_fcff[index]
        assert year_result.pv_fcff.amount == expected_pv_fcff[index]

    assert result.terminal_value.amount == Decimal("2059.13")
    assert result.pv_terminal_value.amount == Decimal("1547.05")
    assert result.enterprise_value.amount == Decimal("1906.40")
    assert result.equity_value.amount == Decimal("1956.40")
    assert result.implied_value_per_share.amount == Decimal("19.56")


def test_negative_fcff_year_is_allowed() -> None:
    """A forecast year where capex exceeds NOPAT + D&A produces a negative FCFF (spec Edge Cases)."""
    assumptions = DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=_money("100"),
                depreciation_and_amortization=_money("0"),
                capital_expenditure=_money("50"),
                change_in_net_working_capital=_money("0"),
            )
        ],
        operating_margin=Decimal("0.10"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal("0.02"),
        cash=_money("0"),
        debt=_money("0"),
        shares_outstanding=Decimal(10),
    )

    result = compute_dcf(assumptions)

    assert result.per_year[0].fcff.amount == Decimal("-40.00")
    assert result.per_year[0].pv_fcff.amount < 0


def test_negative_equity_value_and_implied_value_per_share_are_allowed() -> None:
    """Debt exceeding Enterprise Value + Cash produces a negative Equity Value (spec Edge Cases)."""
    assumptions = DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=_money("1000"),
                depreciation_and_amortization=_money("0"),
                capital_expenditure=_money("0"),
                change_in_net_working_capital=_money("0"),
            )
        ],
        operating_margin=Decimal("0.10"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal("0.02"),
        cash=_money("0"),
        debt=_money("1000000"),
        shares_outstanding=Decimal(10),
    )

    result = compute_dcf(assumptions)

    assert result.equity_value.amount < 0
    assert result.implied_value_per_share.amount < 0


def test_negative_terminal_growth_rate_is_allowed() -> None:
    """A declining perpetuity (negative terminal growth) is valid as long as it stays below WACC (spec Edge Cases)."""
    assumptions = DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=_money("1000"),
                depreciation_and_amortization=_money("0"),
                capital_expenditure=_money("0"),
                change_in_net_working_capital=_money("0"),
            )
        ],
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal("-0.05"),
        cash=_money("0"),
        debt=_money("0"),
        shares_outstanding=Decimal(10),
    )

    result = compute_dcf(assumptions)

    assert result.terminal_value.amount > 0


def test_round_money_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="not finite"):
        _round_money(Decimal("NaN"), "USD")
    with pytest.raises(ValueError, match="not finite"):
        _round_money(Decimal("Infinity"), "USD")
