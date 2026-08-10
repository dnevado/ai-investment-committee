from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import (
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
)


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


def _evidence() -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )


def _thesis(evidence: Evidence) -> InvestmentThesis:
    return InvestmentThesis(
        summary="Durable moat in EUV lithography",
        supporting_evidence=[evidence],
        key_assumptions=["EUV demand persists"],
        key_risks=["Export restrictions"],
        invalidation_conditions=["Major customer cancels multi-year order"],
    )


def test_assembles_from_company_snapshot_thesis_evidence() -> None:
    evidence = _evidence()
    case = InvestmentCase(
        case_id=uuid4(),
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=_thesis(evidence),
        evidence=[evidence],
    )
    assert case.company.ticker == "ASML"
    assert len(case.financial_snapshots) == 1
    assert case.thesis.summary == "Durable moat in EUV lithography"
    assert case.evidence == [evidence]


def test_exposes_stable_identifier_and_analysis_timestamp() -> None:
    case_id = uuid4()
    evidence = _evidence()
    case = InvestmentCase(
        case_id=case_id,
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=_thesis(evidence),
        evidence=[evidence],
    )
    assert case.case_id == case_id
    assert case.analysis_timestamp is not None
    assert case.analysis_timestamp.tzinfo is not None


@pytest.mark.parametrize("missing_field", ["case_id", "company", "thesis"])
def test_required_field_validation(missing_field: str) -> None:
    evidence = _evidence()
    kwargs = {
        "case_id": uuid4(),
        "company": _company(),
        "financial_snapshots": [_snapshot()],
        "thesis": _thesis(evidence),
        "evidence": [evidence],
    }
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        InvestmentCase(**kwargs)


def test_requires_at_least_one_financial_snapshot() -> None:
    evidence = _evidence()
    with pytest.raises(ValidationError):
        InvestmentCase(
            case_id=uuid4(),
            company=_company(),
            financial_snapshots=[],
            thesis=_thesis(evidence),
            evidence=[evidence],
        )


def test_round_trip_serialization() -> None:
    evidence = _evidence()
    case = InvestmentCase(
        case_id=uuid4(),
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=_thesis(evidence),
        evidence=[evidence],
    )
    restored = InvestmentCase.model_validate(case.model_dump())
    assert restored == case
