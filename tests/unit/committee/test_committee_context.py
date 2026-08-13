from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.committee import CommitteeAdjudicationContext
from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    AnalysisAssessment,
    Company,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
)


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


def _dcf_result() -> object:
    forecast = [
        ForecastYear(
            revenue=Money(amount=Decimal(1000), currency="EUR"),
            depreciation_and_amortization=Money(amount=Decimal(0), currency="EUR"),
            capital_expenditure=Money(amount=Decimal(0), currency="EUR"),
            change_in_net_working_capital=Money(amount=Decimal(0), currency="EUR"),
        )
    ]
    assumptions = DCFAssumptions(
        forecast=forecast,
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal(0),
        cash=Money(amount=Decimal(0), currency="EUR"),
        debt=Money(amount=Decimal(0), currency="EUR"),
        shares_outstanding=Decimal(10),
    )
    return compute_dcf(assumptions)


def _assessment() -> AnalysisAssessment:
    return AnalysisAssessment(assessment_id=uuid4(), conclusion="Assessment.", confidence=0.5)


def test_context_holds_all_four_composed_inputs() -> None:
    case = _investment_case()
    dcf_result = _dcf_result()
    bull = _assessment()
    bear = _assessment()

    context = CommitteeAdjudicationContext(
        investment_case=case, dcf_result=dcf_result, bull_assessment=bull, bear_assessment=bear
    )

    assert context.investment_case == case
    assert context.dcf_result == dcf_result
    assert context.bull_assessment == bull
    assert context.bear_assessment == bear


@pytest.mark.parametrize(
    "missing_field", ["investment_case", "dcf_result", "bull_assessment", "bear_assessment"]
)
def test_context_requires_all_fields(missing_field: str) -> None:
    kwargs = {
        "investment_case": _investment_case(),
        "dcf_result": _dcf_result(),
        "bull_assessment": _assessment(),
        "bear_assessment": _assessment(),
    }
    del kwargs[missing_field]

    with pytest.raises(ValidationError):
        CommitteeAdjudicationContext(**kwargs)


def test_round_trip_serialization() -> None:
    context = CommitteeAdjudicationContext(
        investment_case=_investment_case(),
        dcf_result=_dcf_result(),
        bull_assessment=_assessment(),
        bear_assessment=_assessment(),
    )

    restored = CommitteeAdjudicationContext.model_validate(context.model_dump())

    assert restored == context
