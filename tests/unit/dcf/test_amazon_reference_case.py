"""No-network regression fixture: Amazon's FY2025 reference dataset (User Story 2).

Mirrors the DCFAssumptions built in scripts/mvp_amazon_validation.py. Kept as a
separate, deliberately duplicated fixture (rather than importing the script) so this
test has no dependency on the script's OpenAI-provider setup and stays importable and
runnable with zero network access, per FR-008.
"""

from decimal import Decimal

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import Money

USD = "USD"


def _amazon_assumptions() -> DCFAssumptions:
    return DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=Money(amount=Decimal(795786000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(72978000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(119368000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(22164000000), currency=USD),
            ),
            ForecastYear(
                revenue=Money(amount=Decimal(875365000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(80285000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(105044000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(24384000000), currency=USD),
            ),
            ForecastYear(
                revenue=Money(amount=Decimal(954148000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(87514000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(95415000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(26577000000), currency=USD),
            ),
        ],
        operating_margin=Decimal("0.12"),
        tax_rate=Decimal("0.197"),
        wacc=Decimal("0.09"),
        terminal_growth_rate=Decimal("0.03"),
        cash=Money(amount=Decimal(123029000000), currency=USD),
        debt=Money(amount=Decimal(152987000000), currency=USD),
        shares_outstanding=Decimal(10833000000),
    )


def test_amazon_reference_case_produces_a_plausible_positive_valuation() -> None:
    """The rebalanced Amazon dataset passes the plausibility guard (FR-001, FR-002)
    and produces a strictly positive Enterprise Value, Equity Value, and Implied
    Value Per Share (FR-005, FR-007, SC-002)."""
    result = compute_dcf(_amazon_assumptions())

    assert result.per_year[-1].fcff.amount > 0
    assert result.enterprise_value.amount > 0
    assert result.equity_value.amount > 0
    assert result.implied_value_per_share.amount > 0
