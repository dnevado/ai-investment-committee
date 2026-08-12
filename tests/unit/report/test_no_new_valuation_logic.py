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


def _report() -> CommitteeReport:
    evidence = _evidence()
    thesis = InvestmentThesis(summary="Durable moat in EUV lithography", supporting_evidence=[evidence])
    assessment = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Thesis is well-supported.",
        confidence=0.8,
        supporting_evidence=[evidence.evidence_id],
    )
    decision = CommitteeDecision(
        decision_id=uuid4(),
        recommendation=Recommendation.WATCH,
        rationale="Attractive but priced for perfection.",
        referenced_thesis=thesis,
    )
    return CommitteeReport(
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=thesis,
        dcf_result=_dcf_result(),
        assessment=assessment,
        decision=decision,
    )


def test_rendered_valuation_figures_match_dcf_result_exactly() -> None:
    report = _report()

    document = render_report_document(report)

    assert str(report.dcf_result.enterprise_value.amount) in document
    assert str(report.dcf_result.equity_value.amount) in document
    assert str(report.dcf_result.implied_value_per_share.amount) in document
    assert str(report.dcf_result.terminal_value.amount) in document
    assert str(report.dcf_result.pv_terminal_value.amount) in document
    for year in report.dcf_result.per_year:
        assert str(year.fcff.amount) in document
        assert str(year.pv_fcff.amount) in document


def test_recommendation_is_never_altered() -> None:
    original_recommendation = Recommendation.AVOID
    evidence = _evidence()
    thesis = InvestmentThesis(summary="Weak thesis", supporting_evidence=[evidence])
    decision = CommitteeDecision(
        decision_id=uuid4(),
        recommendation=original_recommendation,
        rationale="Structural risks outweigh the upside.",
        referenced_thesis=thesis,
    )
    report = CommitteeReport(
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=thesis,
        dcf_result=_dcf_result(),
        assessment=AnalysisAssessment(
            assessment_id=uuid4(), conclusion="Weak thesis.", confidence=0.3
        ),
        decision=decision,
    )

    document = render_report_document(report)

    assert report.decision.recommendation is original_recommendation
    assert original_recommendation.value in document
