from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from aic.dcf.assumptions import DCFAssumptions
from aic.dcf.result import DCFResult, YearResult
from aic.domain import Money, ValuationResult

_CENTS = Decimal("0.01")


def _round_money(amount: Decimal, currency: str) -> Money:
    if not amount.is_finite():
        raise ValueError(f"Computed value is not finite: {amount}")
    return Money(
        amount=amount.quantize(_CENTS, rounding=ROUND_HALF_UP), currency=currency
    )


def compute_dcf(assumptions: DCFAssumptions) -> DCFResult:
    currency = assumptions.forecast[0].revenue.currency
    one = Decimal(1)

    unrounded_fcff: list[Decimal] = []
    unrounded_pv_fcff: list[Decimal] = []
    year_results: list[YearResult] = []

    for year, item in enumerate(assumptions.forecast, start=1):
        ebit = item.revenue.amount * assumptions.operating_margin
        nopat = ebit * (one - assumptions.tax_rate)
        fcff = (
            nopat
            + item.depreciation_and_amortization.amount
            - item.capital_expenditure.amount
            - item.change_in_net_working_capital.amount
        )
        pv_fcff = fcff / (one + assumptions.wacc) ** year

        unrounded_fcff.append(fcff)
        unrounded_pv_fcff.append(pv_fcff)
        year_results.append(
            YearResult(
                year=year,
                fcff=_round_money(fcff, currency),
                pv_fcff=_round_money(pv_fcff, currency),
            )
        )

    forecast_years = len(assumptions.forecast)
    fcff_final = unrounded_fcff[-1]

    terminal_value = (
        fcff_final
        * (one + assumptions.terminal_growth_rate)
        / (assumptions.wacc - assumptions.terminal_growth_rate)
    )
    pv_terminal_value = terminal_value / (one + assumptions.wacc) ** forecast_years

    enterprise_value = sum(unrounded_pv_fcff, Decimal(0)) + pv_terminal_value
    equity_value = enterprise_value + assumptions.cash.amount - assumptions.debt.amount
    implied_value_per_share = equity_value / assumptions.shares_outstanding

    return DCFResult(
        per_year=year_results,
        terminal_value=_round_money(terminal_value, currency),
        pv_terminal_value=_round_money(pv_terminal_value, currency),
        enterprise_value=_round_money(enterprise_value, currency),
        equity_value=_round_money(equity_value, currency),
        implied_value_per_share=_round_money(implied_value_per_share, currency),
    )


def to_valuation_result(
    result: DCFResult,
    *,
    valuation_id: UUID,
    valuation_date: date,
    confidence: float,
    method: str = "DCF (FCFF)",
    assumption_evidence_refs: list[UUID] | None = None,
) -> ValuationResult:
    return ValuationResult(
        valuation_id=valuation_id,
        method=method,
        valuation_date=valuation_date,
        estimated_value=result.implied_value_per_share,
        confidence=confidence,
        assumption_evidence_refs=assumption_evidence_refs or [],
    )
