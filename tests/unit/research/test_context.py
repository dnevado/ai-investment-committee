from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    Company,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
)
from aic.research import ResearchContext


def _investment_case() -> InvestmentCase:
    company = Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )
    snapshot = FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
    )
    return InvestmentCase(
        case_id=uuid4(),
        company=company,
        financial_snapshots=[snapshot],
        thesis=InvestmentThesis(summary="placeholder"),
    )


def _dcf_result_currency(currency: str) -> object:
    forecast = [
        ForecastYear(
            revenue=Money(amount=Decimal(1000), currency=currency),
            depreciation_and_amortization=Money(amount=Decimal(0), currency=currency),
            capital_expenditure=Money(amount=Decimal(0), currency=currency),
            change_in_net_working_capital=Money(amount=Decimal(0), currency=currency),
        )
    ]
    assumptions = DCFAssumptions(
        forecast=forecast,
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal(0),
        cash=Money(amount=Decimal(0), currency=currency),
        debt=Money(amount=Decimal(0), currency=currency),
        shares_outstanding=Decimal(10),
    )
    return compute_dcf(assumptions)


def test_research_context_holds_investment_case_and_dcf_result() -> None:
    case = _investment_case()
    dcf_result = _dcf_result_currency("EUR")

    context = ResearchContext(investment_case=case, dcf_result=dcf_result)

    assert context.investment_case == case
    assert context.dcf_result == dcf_result


def test_research_context_requires_both_fields() -> None:
    with pytest.raises(ValidationError):
        ResearchContext(investment_case=_investment_case())  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        ResearchContext(dcf_result=_dcf_result_currency("EUR"))  # type: ignore[call-arg]
