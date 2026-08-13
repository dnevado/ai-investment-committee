from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.dcf import DCFAssumptions, ForecastYear
from aic.domain import Company, FinancialSnapshot, Money
from aic.workflow import WorkflowInput


def _company() -> Company:
    return Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )


def _snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
    )


def _assumptions() -> DCFAssumptions:
    forecast = [
        ForecastYear(
            revenue=Money(amount=Decimal(1000), currency="EUR"),
            depreciation_and_amortization=Money(amount=Decimal(0), currency="EUR"),
            capital_expenditure=Money(amount=Decimal(0), currency="EUR"),
            change_in_net_working_capital=Money(amount=Decimal(0), currency="EUR"),
        )
    ]
    return DCFAssumptions(
        forecast=forecast,
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal(0),
        cash=Money(amount=Decimal(0), currency="EUR"),
        debt=Money(amount=Decimal(0), currency="EUR"),
        shares_outstanding=Decimal(10),
    )


def test_workflow_input_holds_all_composed_values() -> None:
    company = _company()
    snapshot = _snapshot()
    assumptions = _assumptions()

    workflow_input = WorkflowInput(
        company=company,
        financial_snapshots=[snapshot],
        evidence=[],
        dcf_assumptions=assumptions,
    )

    assert workflow_input.company == company
    assert workflow_input.financial_snapshots == [snapshot]
    assert workflow_input.evidence == []
    assert workflow_input.dcf_assumptions == assumptions


@pytest.mark.parametrize("missing_field", ["company", "financial_snapshots", "dcf_assumptions"])
def test_workflow_input_requires_fields(missing_field: str) -> None:
    kwargs = {
        "company": _company(),
        "financial_snapshots": [_snapshot()],
        "evidence": [],
        "dcf_assumptions": _assumptions(),
    }
    del kwargs[missing_field]

    with pytest.raises(ValidationError):
        WorkflowInput(**kwargs)


def test_workflow_input_rejects_empty_financial_snapshots() -> None:
    with pytest.raises(ValidationError):
        WorkflowInput(
            company=_company(),
            financial_snapshots=[],
            evidence=[],
            dcf_assumptions=_assumptions(),
        )


def test_round_trip_serialization() -> None:
    workflow_input = WorkflowInput(
        company=_company(),
        financial_snapshots=[_snapshot()],
        evidence=[],
        dcf_assumptions=_assumptions(),
    )

    restored = WorkflowInput.model_validate(workflow_input.model_dump())

    assert restored == workflow_input
