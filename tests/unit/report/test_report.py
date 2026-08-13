from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    AnalysisAssessment,
    CommitteeDecision,
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentThesis,
    Money,
    Recommendation,
)
from aic.report import CommitteeReport


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


def _assessment(evidence: Evidence) -> AnalysisAssessment:
    return AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Thesis is well-supported.",
        confidence=0.8,
        arguments=["Structural demand for EUV"],
        supporting_evidence=[evidence.evidence_id],
        assumptions=["EUV demand persists"],
        risks=["Export restrictions"],
    )


def _decision(
    thesis: InvestmentThesis, dissent: list[str] | None = None
) -> CommitteeDecision:
    return CommitteeDecision(
        decision_id=uuid4(),
        recommendation=Recommendation.WATCH,
        rationale="Attractive but priced for perfection.",
        referenced_thesis=thesis,
        dissent=dissent or [],
    )


def _full_kwargs() -> dict[str, object]:
    evidence = _evidence()
    thesis = _thesis(evidence)
    return {
        "company": _company(),
        "financial_snapshots": [_snapshot()],
        "thesis": thesis,
        "dcf_result": _dcf_result(),
        "assessment": _assessment(evidence),
        "decision": _decision(thesis),
    }


def test_valid_construction_preserves_all_composed_values() -> None:
    kwargs = _full_kwargs()

    report = CommitteeReport(**kwargs)

    assert report.company == kwargs["company"]
    assert report.financial_snapshots == kwargs["financial_snapshots"]
    assert report.thesis == kwargs["thesis"]
    assert report.dcf_result == kwargs["dcf_result"]
    assert report.assessment == kwargs["assessment"]
    assert report.decision == kwargs["decision"]


@pytest.mark.parametrize(
    "missing_field",
    [
        "company",
        "financial_snapshots",
        "thesis",
        "dcf_result",
        "assessment",
        "decision",
    ],
)
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _full_kwargs()
    del kwargs[missing_field]

    with pytest.raises(ValidationError):
        CommitteeReport(**kwargs)


def test_financial_snapshots_rejects_empty_list() -> None:
    kwargs = _full_kwargs()
    kwargs["financial_snapshots"] = []

    with pytest.raises(ValidationError):
        CommitteeReport(**kwargs)


def test_preserves_dissent_when_present() -> None:
    kwargs = _full_kwargs()
    thesis = kwargs["thesis"]
    assert isinstance(thesis, InvestmentThesis)
    kwargs["decision"] = _decision(
        thesis, dissent=["Bear case underweights export risk."]
    )

    report = CommitteeReport(**kwargs)

    assert report.decision.dissent == ["Bear case underweights export risk."]


def test_preserves_absence_of_dissent() -> None:
    kwargs = _full_kwargs()

    report = CommitteeReport(**kwargs)

    assert report.decision.dissent == []


def test_preserves_multiple_snapshots_with_differing_periods_and_currencies() -> None:
    kwargs = _full_kwargs()
    eur_snapshot = _snapshot()
    usd_snapshot = FinancialSnapshot(
        as_of=date(2025, 12, 31),
        revenue=Money(amount=Decimal(7000000000), currency="USD"),
    )
    kwargs["financial_snapshots"] = [eur_snapshot, usd_snapshot]

    report = CommitteeReport(**kwargs)

    assert report.financial_snapshots == [eur_snapshot, usd_snapshot]
    assert report.financial_snapshots[0].revenue.currency == "EUR"
    assert report.financial_snapshots[1].revenue.currency == "USD"
    assert report.financial_snapshots[0].as_of != report.financial_snapshots[1].as_of


def test_round_trip_serialization() -> None:
    report = CommitteeReport(**_full_kwargs())

    restored = CommitteeReport.model_validate(report.model_dump())

    assert restored == report
