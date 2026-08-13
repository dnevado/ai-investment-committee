from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.bullbear import BullBearContext
from aic.domain import (
    Company,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
    ValuationResult,
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


def _valuation_result() -> ValuationResult:
    return ValuationResult(
        valuation_id=uuid4(),
        method="DCF (FCFF)",
        valuation_date=date(2026, 3, 31),
        estimated_value=Money(amount=Decimal("850.00"), currency="EUR"),
        confidence=0.7,
    )


def test_context_holds_investment_case_and_valuation_result() -> None:
    case = _investment_case()
    valuation = _valuation_result()

    context = BullBearContext(investment_case=case, valuation_result=valuation)

    assert context.investment_case == case
    assert context.valuation_result == valuation


@pytest.mark.parametrize("missing_field", ["investment_case", "valuation_result"])
def test_context_requires_both_fields(missing_field: str) -> None:
    kwargs = {
        "investment_case": _investment_case(),
        "valuation_result": _valuation_result(),
    }
    del kwargs[missing_field]

    with pytest.raises(ValidationError):
        BullBearContext(**kwargs)


def test_round_trip_serialization() -> None:
    context = BullBearContext(
        investment_case=_investment_case(), valuation_result=_valuation_result()
    )

    restored = BullBearContext.model_validate(context.model_dump())

    assert restored == context
