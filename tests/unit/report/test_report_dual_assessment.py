from datetime import date
from decimal import Decimal
from uuid import uuid4

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
from aic.report import CommitteeReport, render_report_document


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


def _base_report_kwargs(evidence: Evidence) -> dict:
    thesis = InvestmentThesis(summary="Durable moat in EUV lithography", supporting_evidence=[evidence])
    assessment = AnalysisAssessment(
        assessment_id=uuid4(), conclusion="Thesis is well-supported.", confidence=0.8
    )
    decision = CommitteeDecision(
        decision_id=uuid4(),
        recommendation=Recommendation.WATCH,
        rationale="Attractive but priced for perfection.",
        referenced_thesis=thesis,
    )
    return {
        "company": _company(),
        "financial_snapshots": [_snapshot()],
        "thesis": thesis,
        "dcf_result": _dcf_result(),
        "assessment": assessment,
        "decision": decision,
    }


def test_committee_report_defaults_bull_and_bear_assessment_to_none() -> None:
    report = CommitteeReport(**_base_report_kwargs(_evidence()))

    assert report.bull_assessment is None
    assert report.bear_assessment is None


def test_committee_report_accepts_bull_and_bear_assessment() -> None:
    bull = AnalysisAssessment(assessment_id=uuid4(), conclusion="Outperform.", confidence=0.75)
    bear = AnalysisAssessment(assessment_id=uuid4(), conclusion="Underperform risk.", confidence=0.4)
    report = CommitteeReport(
        **_base_report_kwargs(_evidence()), bull_assessment=bull, bear_assessment=bear
    )

    assert report.bull_assessment == bull
    assert report.bear_assessment == bear


def test_render_report_document_unchanged_when_bull_bear_absent() -> None:
    report = CommitteeReport(**_base_report_kwargs(_evidence()))

    document = render_report_document(report)

    assert "## Committee Assessment" in document
    assert "Bull Case Assessment" not in document
    assert "Bear Case Assessment" not in document
    assert report.assessment.conclusion in document


def test_render_report_document_shows_both_sections_when_bull_bear_present() -> None:
    bull = AnalysisAssessment(assessment_id=uuid4(), conclusion="Outperform.", confidence=0.75)
    bear = AnalysisAssessment(assessment_id=uuid4(), conclusion="Underperform risk.", confidence=0.4)
    report = CommitteeReport(
        **_base_report_kwargs(_evidence()), bull_assessment=bull, bear_assessment=bear
    )

    document = render_report_document(report)

    assert "## Bull Case Assessment" in document
    assert "## Bear Case Assessment" in document
    assert "## Committee Assessment" not in document
    assert bull.conclusion in document
    assert bear.conclusion in document
